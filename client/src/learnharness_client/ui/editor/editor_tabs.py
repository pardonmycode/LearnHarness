"""Multi-file editor tabs, atomic saving, watchers, and recovery."""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QFileSystemWatcher, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMessageBox, QTabWidget, QVBoxLayout, QWidget

from learnharness_client.config import AppSettings, app_data_dir
from learnharness_client.domain.backup import BackupManager
from learnharness_client.domain.file_store import FileStore, FileStoreError, SaveConflict
from learnharness_client.domain.project import GodotProject
from learnharness_client.domain.recovery import RecoveryManager
from learnharness_client.domain.script_document import ScriptDocument, sha256_bytes

from ...texts import T
from ..dialogs.conflict_dialog import ConflictDialog
from ..dialogs.recovery_dialog import RecoveryDialog
from .code_editor import CodeEditor
from .find_bar import FindBar

LOG = logging.getLogger(__name__)


class EditorTabs(QWidget):
    status_message = pyqtSignal(str)
    current_file_changed = pyqtSignal(str)
    cursor_changed = pyqtSignal(int, int)
    # file name, old text, new text – emitted after the LearnAgent wrote a file
    generated_file_applied = pyqtSignal(str, str, str)

    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.project: GodotProject | None = None
        self.store: FileStore | None = None
        self.recovery = RecoveryManager(app_data_dir())
        self.documents: dict[CodeEditor, ScriptDocument] = {}
        self.paths: dict[Path, CodeEditor] = {}
        self.tabs = QTabWidget()
        self.tabs.setObjectName("editorTabs")
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._tab_changed)
        self.find_bar = FindBar()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.find_bar)
        layout.addWidget(self.tabs)
        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self._watcher_changed)
        self._pending_checks: set[Path] = set()
        self._watch_timer = QTimer(self)
        self._watch_timer.setSingleShot(True)
        self._watch_timer.setInterval(350)
        self._watch_timer.timeout.connect(self._run_pending_checks)
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(30_000)
        self.autosave_timer.timeout.connect(self.write_recovery_drafts)
        self.autosave_timer.start()
        # Optional automatic saving shortly after typing (setting "Automatisch speichern").
        self.quick_save_timer = QTimer(self)
        self.quick_save_timer.setSingleShot(True)
        self.quick_save_timer.setInterval(2_000)
        self.quick_save_timer.timeout.connect(self.autosave_dirty)
        app = QApplication.instance()
        if app is not None:
            app.applicationStateChanged.connect(lambda _state: self.check_all_external_changes())

    def set_project(self, project: GodotProject) -> None:
        if self.project and not self.confirm_close_all():
            return
        self.project = project
        self.store = FileStore(
            project.guard,
            BackupManager(app_data_dir(), project.project_id),
        )
        self._offer_recovery()

    def open_file(self, path: Path) -> CodeEditor | None:
        if not self.store or not self.project:
            return None
        try:
            allowed = self.project.guard.ensure_allowed(path)
            if allowed in self.paths:
                editor = self.paths[allowed]
                self.tabs.setCurrentWidget(editor)
                return editor
            document = self.store.load(allowed)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, T.FILE_NOT_OPENED, str(exc))
            return None
        editor = CodeEditor(font_size=self.settings.font_size)
        editor.setPlainText(document.text)
        editor.document().setModified(False)
        editor.textChanged.connect(lambda current=editor: self._text_changed(current))
        editor.cursor_location_changed.connect(self.cursor_changed)
        editor.font_size_changed.connect(self._remember_font_size)
        self.documents[editor] = document
        self.paths[allowed] = editor
        index = self.tabs.addTab(editor, allowed.name)
        self.tabs.setTabToolTip(index, str(allowed.relative_to(self.project.root)))
        self.tabs.setCurrentIndex(index)
        self.watcher.addPath(str(allowed))
        return editor

    def create_file(self, relative_path: Path) -> CodeEditor | None:
        if not self.store:
            return None
        try:
            document = self.store.create(relative_path)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, T.FILE_NOT_CREATED, str(exc))
            return None
        return self.open_file(document.path)

    def apply_generated_file(self, relative_path: str, content: str) -> bool:
        """Write server-generated code only after MainWindow has accepted a correct review."""
        if not self.project or not self.store:
            return False
        try:
            path = self.project.guard.ensure_allowed(relative_path, must_exist=False)
        except ValueError as exc:
            QMessageBox.warning(self, T.AGENT_CODE_NOT_WRITTEN, str(exc))
            return False
        if not path.exists():
            try:
                document = self.store.create(relative_path, content)
            except (OSError, ValueError) as exc:
                QMessageBox.warning(self, T.AGENT_CODE_NOT_WRITTEN, str(exc))
                return False
            self.open_file(document.path)
            self.status_message.emit(T.AGENT_CREATED_FILE.format(file=document.path.name))
            self.generated_file_applied.emit(document.path.name, "", content)
            return True

        editor = self.open_file(path)
        if editor is None:
            return False
        document = self.documents[editor]
        if document.dirty:
            QMessageBox.warning(
                self,
                T.UNSAVED_OWN_CODE_TITLE,
                T.UNSAVED_OWN_CODE,
            )
            return False
        old_text = editor.toPlainText()
        # One undo step: the child can press Strg+Z to see their previous code again.
        editor.replace_all_text(content)
        if not self.save_editor(editor):
            return False
        self.status_message.emit(T.AGENT_WROTE_FILE.format(file=document.path.name))
        self.generated_file_applied.emit(document.path.name, old_text, content)
        return True

    def backups_for_current(self) -> list[Path]:
        document = self.current_document()
        if not document or not self.project or not self.store:
            return []
        relative = document.path.relative_to(self.project.root)
        return self.store.backup_manager.list_for(relative)

    def restore_into_current(self, text: str) -> bool:
        """Put an older version into the editor as one undo step; saving stays explicit."""
        editor = self.current_editor()
        if editor is None:
            return False
        editor.replace_all_text(text)
        return True

    def current_editor(self) -> CodeEditor | None:
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, CodeEditor) else None

    def current_document(self) -> ScriptDocument | None:
        editor = self.current_editor()
        return self.documents.get(editor) if editor else None

    def _text_changed(self, editor: CodeEditor) -> None:
        document = self.documents.get(editor)
        if not document:
            return
        document.update_text(editor.toPlainText())
        self._update_title(editor)
        if document.dirty and self.settings.autosave:
            self.quick_save_timer.start()

    def autosave_dirty(self) -> None:
        """Save quietly; files changed outside are left for the normal conflict check."""
        if not self.store or not self.settings.autosave:
            return
        for editor, document in list(self.documents.items()):
            if not document.dirty or document.deleted_externally:
                continue
            try:
                if self.store.has_external_change(document):
                    continue
            except (OSError, ValueError):
                continue
            if self.save_editor(editor, quiet=True):
                self.status_message.emit(T.AUTOSAVED.format(file=document.path.name))

    def _update_title(self, editor: CodeEditor) -> None:
        index = self.tabs.indexOf(editor)
        document = self.documents[editor]
        marker = " •" if document.dirty else ""
        self.tabs.setTabText(index, f"{document.path.name}{marker}")

    def save_current(self) -> bool:
        editor = self.current_editor()
        return self.save_editor(editor) if editor else True

    def save_editor(self, editor: CodeEditor | None, *, quiet: bool = False) -> bool:
        if not editor or not self.store or not self.project:
            return True
        document = self.documents[editor]
        document.update_text(editor.toPlainText())
        try:
            self.store.save(document)
        except SaveConflict as conflict:
            disk_text = T.CONFLICT_DELETED
            if conflict.disk_bytes is not None:
                disk_text = conflict.disk_bytes.decode("utf-8-sig", errors="replace")
            choice = ConflictDialog.choose(document.text, disk_text, self)
            if choice == ConflictDialog.KEEP_MINE:
                try:
                    self.store.save(document, force=True)
                except FileStoreError as exc:
                    self._save_error(exc)
                    return False
            elif choice == ConflictDialog.LOAD_DISK:
                return self._reload(editor, discard_local=True)
            else:
                return False
        except FileStoreError as exc:
            self._save_error(exc)
            return False
        self.recovery.clear(self.project.project_id, document.path.relative_to(self.project.root))
        editor.document().setModified(False)
        self._update_title(editor)
        self._ensure_watched(document.path)
        if not quiet:
            self.status_message.emit(T.SAVED.format(file=document.path.name))
        return True

    def _save_error(self, error: Exception) -> None:
        self.write_recovery_drafts()
        QMessageBox.critical(
            self,
            T.SAVE_FAILED_TITLE,
            T.SAVE_FAILED.format(error=error),
        )

    def _reload(self, editor: CodeEditor, *, discard_local: bool) -> bool:
        if not self.store:
            return False
        old = self.documents[editor]
        if old.dirty and not discard_local:
            return False
        try:
            fresh = self.store.load(old.path)
        except OSError as exc:
            self.status_message.emit(str(exc))
            return False
        cursor_position = editor.textCursor().position()
        scroll_bar = editor.verticalScrollBar()
        scroll_value = scroll_bar.value() if scroll_bar else 0
        editor.blockSignals(True)
        editor.setPlainText(fresh.text)
        editor.blockSignals(False)
        cursor = editor.textCursor()
        cursor.setPosition(min(cursor_position, len(fresh.text)))
        editor.setTextCursor(cursor)
        if scroll_bar:
            # Keep the view where the child was reading instead of jumping to the cursor.
            scroll_bar.setValue(min(scroll_value, scroll_bar.maximum()))
        self.documents[editor] = fresh
        self._update_title(editor)
        self._ensure_watched(fresh.path)
        self.status_message.emit(T.RELOADED_FROM_GODOT.format(file=fresh.path.name))
        return True

    def _watcher_changed(self, path_text: str) -> None:
        # Debounced via a child timer: it dies with this widget, so no check can run late.
        self._pending_checks.add(Path(path_text))
        self._watch_timer.start()

    def _run_pending_checks(self) -> None:
        pending, self._pending_checks = self._pending_checks, set()
        for path in pending:
            self._check_path(path)

    def _check_path(self, path: Path) -> None:
        editor = self.paths.get(path)
        if not editor or not self.store:
            return
        document = self.documents[editor]
        if not path.exists():
            document.deleted_externally = True
            self.status_message.emit(T.DELETED_EXTERNALLY.format(file=path.name))
            return
        self._ensure_watched(path)
        if not self.store.has_external_change(document):
            return
        if not document.dirty:
            self._reload(editor, discard_local=True)
            return
        disk_bytes = path.read_bytes()
        disk_text = disk_bytes.decode("utf-8-sig", errors="replace")
        choice = ConflictDialog.choose(document.text, disk_text, self)
        if choice == ConflictDialog.LOAD_DISK:
            self._reload(editor, discard_local=True)
        elif choice == ConflictDialog.KEEP_MINE:
            document.disk_hash = sha256_bytes(disk_bytes)
            document.disk_mtime_ns = path.stat().st_mtime_ns
            self.status_message.emit(T.KEEPING_MY_VERSION)

    def _ensure_watched(self, path: Path) -> None:
        if path.exists() and str(path) not in self.watcher.files():
            self.watcher.addPath(str(path))

    def check_all_external_changes(self) -> None:
        for path in list(self.paths):
            self._check_path(path)

    def write_recovery_drafts(self) -> None:
        if not self.project:
            return
        for document in self.documents.values():
            if document.dirty:
                relative = document.path.relative_to(self.project.root)
                try:
                    self.recovery.write(self.project.project_id, relative, document)
                except OSError:
                    LOG.exception("Could not write recovery draft for %s", relative)

    def _offer_recovery(self) -> None:
        if not self.project:
            return
        for draft in self.recovery.list_for_project(self.project.project_id):
            try:
                content = draft.content_path.read_text(encoding="utf-8")
            except OSError:
                continue
            dialog = RecoveryDialog(str(draft.relative_path), content, self)
            dialog.exec()
            if dialog.choice == RecoveryDialog.DISCARD:
                self.recovery.clear(draft.project_id, draft.relative_path)
            elif dialog.choice == RecoveryDialog.RESTORE:
                path = self.project.root / draft.relative_path
                editor = self.open_file(path)
                if editor:
                    editor.setPlainText(content)

    def close_tab(self, index: int) -> bool:
        editor = self.tabs.widget(index)
        if not isinstance(editor, CodeEditor):
            return True
        document = self.documents[editor]
        if document.dirty:
            answer = QMessageBox.question(
                self,
                T.UNSAVED_CHANGES_TITLE,
                T.UNSAVED_CHANGES.format(file=document.path.name),
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )
            if answer == QMessageBox.StandardButton.Cancel:
                return False
            if answer == QMessageBox.StandardButton.Save and not self.save_editor(editor):
                return False
            if answer == QMessageBox.StandardButton.Discard and self.project:
                self.recovery.clear(
                    self.project.project_id, document.path.relative_to(self.project.root)
                )
        self.watcher.removePath(str(document.path))
        self.paths.pop(document.path, None)
        self.documents.pop(editor, None)
        self.tabs.removeTab(index)
        editor.deleteLater()
        return True

    def confirm_close_all(self) -> bool:
        return all(self.close_tab(index) for index in reversed(range(self.tabs.count())))

    def _tab_changed(self, _index: int) -> None:
        editor = self.current_editor()
        self.find_bar.attach(editor)
        document = self.current_document()
        self.current_file_changed.emit(document.path.name if document else T.NO_FILE)

    def open_find(self, replace: bool = False) -> None:
        self.find_bar.attach(self.current_editor())
        self.find_bar.open_find(replace)

    def goto_line(self, line: int) -> None:
        editor = self.current_editor()
        if editor:
            editor.goto_line(line)

    def _remember_font_size(self, size: int) -> None:
        self.settings.font_size = size
