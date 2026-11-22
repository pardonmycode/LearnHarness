"""Saving, autosave and crash recovery."""

from __future__ import annotations

import logging

from PyQt6.QtWidgets import QMessageBox

from learnharness_client.domain.file_store import FileStoreError, SaveConflict

from ....texts import T
from ...dialogs.conflict_dialog import ConflictDialog
from ...dialogs.recovery_dialog import RecoveryDialog
from ..code_editor import CodeEditor

LOG = logging.getLogger(__name__)


class TabSaving:
    """Saving and recovery drafts."""

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
