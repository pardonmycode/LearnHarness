"""Problems from Godot, Python or server review."""

from __future__ import annotations

import re
from dataclasses import dataclass

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...texts import T

_GODOT_LOCATION = re.compile(r"res://([^:\s]+\.gd):(\d+)", re.IGNORECASE)
_PYTHON_LOCATION = re.compile(r'File "([^"]+\.py)", line (\d+)', re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class Problem:
    file: str
    line: int
    message: str
    source: str


class ProblemsPanel(QWidget):
    problem_activated = pyqtSignal(str, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.language = "gdscript"
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.error_input = QLineEdit()
        self.error_input.setPlaceholderText(T.PROBLEM_INPUT_PLACEHOLDER)
        self.error_input.setAccessibleName(T.PROBLEM_INPUT_A11Y)
        add_button = QPushButton(T.PROBLEM_ADD)
        row.addWidget(self.error_input, 1)
        row.addWidget(add_button)
        self.list = QListWidget()
        self.list.setAccessibleName(T.PROBLEM_LIST_A11Y)
        layout.addLayout(row)
        layout.addWidget(self.list)
        add_button.clicked.connect(self.add_from_input)
        self.error_input.returnPressed.connect(self.add_from_input)
        self.list.itemActivated.connect(self._activate)

    def set_language(self, language: str) -> None:
        self.language = language
        python = language == "python"
        self.error_input.setPlaceholderText(
            T.PROBLEM_INPUT_PLACEHOLDER_PYTHON if python else T.PROBLEM_INPUT_PLACEHOLDER
        )
        self.error_input.setAccessibleName(
            T.PROBLEM_INPUT_A11Y_PYTHON if python else T.PROBLEM_INPUT_A11Y
        )

    def add_from_input(self) -> None:
        text = self.error_input.text().strip()
        if not text:
            return
        if self.language == "python":
            # In a traceback the last location is where the error happened.
            matches = list(_PYTHON_LOCATION.finditer(text))
            match = matches[-1] if matches else None
            source = T.SOURCE_PYTHON
        else:
            match = _GODOT_LOCATION.search(text)
            source = T.SOURCE_GODOT
        problem = Problem(
            file=match.group(1) if match else "",
            line=int(match.group(2)) if match else 0,
            message=text,
            source=source,
        )
        self.add_problem(problem)
        self.error_input.clear()

    def problems(self) -> list[Problem]:
        found: list[Problem] = []
        for row in range(self.list.count()):
            item = self.list.item(row)
            problem = item.data(Qt.ItemDataRole.UserRole) if item else None
            if isinstance(problem, Problem):
                found.append(problem)
        return found

    def add_problem(self, problem: Problem) -> bool:
        """Adds the problem unless the same one is already listed."""
        if problem in self.problems():
            return False
        location = f"{problem.file}:{problem.line} – " if problem.file else ""
        item = QListWidgetItem(f"[{problem.source}] {location}{problem.message}")
        item.setData(Qt.ItemDataRole.UserRole, problem)
        self.list.addItem(item)
        return True

    def clear_source(self, source: str) -> None:
        for row in reversed(range(self.list.count())):
            item = self.list.item(row)
            problem = item.data(Qt.ItemDataRole.UserRole) if item else None
            if isinstance(problem, Problem) and problem.source == source:
                self.list.takeItem(row)

    def _activate(self, item: QListWidgetItem) -> None:
        problem = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(problem, Problem) and problem.file:
            self.problem_activated.emit(problem.file, problem.line)

    def last_error(self) -> str | None:
        if self.list.count() == 0:
            return None
        problem = self.list.item(self.list.count() - 1).data(Qt.ItemDataRole.UserRole)
        return problem.message if isinstance(problem, Problem) else None
