"""Noticing and reloading changes made outside the editor."""

from __future__ import annotations

from pathlib import Path

from learnharness_client.domain.script_document import sha256_bytes

from ....texts import T
from ...dialogs.conflict_dialog import ConflictDialog
from ..code_editor import CodeEditor


class TabWatching:
    """External changes."""

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
        self.status_message.emit(T.RELOADED_FROM_DISK.format(file=fresh.path.name))
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
