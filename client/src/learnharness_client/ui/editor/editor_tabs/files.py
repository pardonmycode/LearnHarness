"""Opening, creating, closing and generated files."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QMessageBox

from learnharness_client.domain.limits import MAX_FILE_CONTEXT

from ....texts import T
from ..code_editor import CodeEditor


class TabFiles:
    """Files shown in tabs."""

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
        editor = CodeEditor(font_size=self.settings.font_size, language=self.project.language)
        editor.adopt_indentation(document.text)
        editor.explain_requested.connect(self.explain_requested)
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

    def apply_generated_file(
        self, relative_path: str, content: str, expected_text: str | None = None
    ) -> bool:
        """Write server-generated code only after MainWindow has accepted a correct review.

        expected_text is the script the code was made from; a script changed since then stays."""
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
        if len(editor.toPlainText()) > MAX_FILE_CONTEXT:
            QMessageBox.warning(self, T.FILE_TOO_LONG_TITLE, T.FILE_TOO_LONG)
            return False
        if expected_text is not None and editor.toPlainText() != expected_text:
            QMessageBox.warning(self, T.FILE_CHANGED_TITLE, T.FILE_CHANGED)
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

    def _text_changed(self, editor: CodeEditor) -> None:
        document = self.documents.get(editor)
        if not document:
            return
        document.update_text(editor.toPlainText())
        self._update_title(editor)
        if document.dirty and self.settings.autosave:
            self.quick_save_timer.start()

    def _update_title(self, editor: CodeEditor) -> None:
        index = self.tabs.indexOf(editor)
        document = self.documents[editor]
        marker = " •" if document.dirty else ""
        self.tabs.setTabText(index, f"{document.path.name}{marker}")

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
