"""Syntax checks for Godot and Python, and the Godot log."""

from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox

from learnharness_client.domain.path_guard import fold_case
from learnharness_client.domain.python_check import check_python
from learnharness_client.godot.log_reader import default_log_path, read_recent_errors
from learnharness_client.godot.output_parser import GodotMessage
from learnharness_client.godot.paths import find_godot_on_path

from ...texts import T
from ..panels.problems_panel import Problem


class CheckActions:
    """Syntax checks and log reading."""

    def run_syntax_check(self) -> None:
        document = self.editor_tabs.current_document()
        if not self.project or document is None:
            QMessageBox.information(self, T.SYNTAX_CHECK, T.OPEN_FILE_FIRST)
            return
        if self.project.language == "python":
            self._run_python_check()
            return
        # Without a setting, use Godot from PATH (typical on Linux: godot4 from the package).
        godot = self.settings.godot_path or find_godot_on_path()
        if not godot:
            QMessageBox.information(self, T.SYNTAX_CHECK, T.GODOT_NOT_SET)
            return
        # Godot reads the file from disk, so it must see the same state as the editor.
        if document.dirty and not self.editor_tabs.save_current():
            return
        self._syntax_check_file = document.path.relative_to(self.project.root).as_posix()
        if self.syntax_checker.start(godot, self.project.root, document.path):
            self.statusBar().showMessage(
                T.GODOT_CHECK_RUNNING.format(file=document.path.name), 10_000
            )

    def _run_python_check(self) -> None:
        """Checks the text in the editor; the child's code is parsed but never run."""
        editor = self.editor_tabs.current_editor()
        relative = self._relative_current_file()
        if editor is None or relative is None:
            return
        found = check_python(editor.toPlainText(), relative)
        self.problems_panel.clear_source(T.SOURCE_PYTHON_CHECK)
        editor.set_error_lines([problem.line for problem in found])
        if not found:
            self.statusBar().showMessage(T.PYTHON_CHECK_OK.format(file=relative), 8000)
            return
        for problem in found:
            self.problems_panel.add_problem(
                Problem(relative, problem.line, problem.message, T.SOURCE_PYTHON_CHECK)
            )
        self.problems_dock.setVisible(True)
        self.statusBar().showMessage(T.PYTHON_CHECK_ERROR.format(line=found[0].line), 8000)

    def _syntax_check_finished(self, messages: list[GodotMessage]) -> None:
        file = self._syntax_check_file
        self.problems_panel.clear_source(T.SOURCE_GODOT_CHECK)
        editor = self.editor_tabs.current_editor()
        if editor:
            editor.set_error_lines(
                [m.line for m in messages if fold_case(m.file) == fold_case(file)]
            )
        if not messages:
            self.statusBar().showMessage(T.GODOT_CHECK_OK.format(file=file), 8000)
            return
        self._add_godot_messages(messages, T.SOURCE_GODOT_CHECK)
        self.statusBar().showMessage(T.GODOT_CHECK_ERRORS.format(count=len(messages)), 8000)

    def _syntax_check_failed(self, reason: str) -> None:
        self.statusBar().showMessage(T.GODOT_CHECK_FAILED.format(reason=reason), 8000)

    def read_godot_log(self) -> None:
        if not self.project:
            QMessageBox.information(self, T.READ_GODOT_LOG, T.OPEN_PROJECT_FIRST)
            return
        log_path = default_log_path(self.project.name)
        if log_path is None or not log_path.is_file():
            QMessageBox.information(self, T.READ_GODOT_LOG, T.GODOT_LOG_MISSING)
            return
        try:
            messages = read_recent_errors(log_path)
        except OSError as exc:
            QMessageBox.warning(self, T.READ_GODOT_LOG, str(exc))
            return
        added = self._add_godot_messages(messages, T.SOURCE_GODOT_LOG)
        text = T.GODOT_LOG_FOUND.format(count=added) if added else T.GODOT_LOG_EMPTY
        self.statusBar().showMessage(text, 8000)

    def _add_godot_messages(self, messages: list[GodotMessage], source: str) -> int:
        added = 0
        for message in messages:
            problem = Problem(message.file, message.line, message.message, source)
            if self.problems_panel.add_problem(problem):
                added += 1
        if added:
            self.problems_dock.setVisible(True)
        return added
