"""Multi-file editor tabs, atomic saving, watchers, and recovery."""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QFileSystemWatcher, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication, QTabWidget, QVBoxLayout, QWidget

from learnharness_client.config import AppSettings, app_data_dir
from learnharness_client.domain.backup import BackupManager
from learnharness_client.domain.file_store import FileStore
from learnharness_client.domain.project import Project
from learnharness_client.domain.recovery import RecoveryManager
from learnharness_client.domain.script_document import ScriptDocument

from ....texts import T
from ..code_editor import CodeEditor
from ..find_bar import FindBar
from .files import TabFiles
from .saving import TabSaving
from .watching import TabWatching

__all__ = ["EditorTabs", "LOG"]


LOG = logging.getLogger(__name__)


class EditorTabs(TabFiles, TabSaving, TabWatching, QWidget):
    status_message = pyqtSignal(str)
    current_file_changed = pyqtSignal(str)
    cursor_changed = pyqtSignal(int, int)
    # file name, old text, new text – emitted after the LearnAgent wrote a file
    generated_file_applied = pyqtSignal(str, str, str)
    explain_requested = pyqtSignal()

    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.project: Project | None = None
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

    def set_project(self, project: Project) -> None:
        if self.project and not self.confirm_close_all():
            return
        self.project = project
        self.store = FileStore(
            project.guard,
            BackupManager(app_data_dir(), project.project_id),
        )
        self._offer_recovery()

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
