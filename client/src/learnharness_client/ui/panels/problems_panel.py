"""Problems from Godot or server review."""

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

_GODOT_LOCATION = re.compile(r"res://([^:\s]+\.gd):(\d+)", re.IGNORECASE)


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
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.error_input = QLineEdit()
        self.error_input.setPlaceholderText("Godot-Fehlermeldung hier einfügen …")
        self.error_input.setAccessibleName("Godot-Fehlermeldung einfügen")
        add_button = QPushButton("Fehler hinzufügen")
        row.addWidget(self.error_input, 1)
        row.addWidget(add_button)
        self.list = QListWidget()
        self.list.setAccessibleName("Liste der Probleme")
        layout.addLayout(row)
        layout.addWidget(self.list)
        add_button.clicked.connect(self.add_from_input)
        self.error_input.returnPressed.connect(self.add_from_input)
        self.list.itemActivated.connect(self._activate)

    def add_from_input(self) -> None:
        text = self.error_input.text().strip()
        if not text:
            return
        match = _GODOT_LOCATION.search(text)
        problem = Problem(
            file=match.group(1) if match else "",
            line=int(match.group(2)) if match else 0,
            message=text,
            source="Godot",
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
