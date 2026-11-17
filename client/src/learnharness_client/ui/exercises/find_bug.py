"""Select one or more suspicious code lines."""

from __future__ import annotations

from learnharness_protocol import FindBugExercise, Submission
from PyQt6.QtWidgets import QAbstractItemView, QLineEdit, QListWidget, QListWidgetItem

from .base import ExerciseWidget


class FindBugWidget(ExerciseWidget):
    def __init__(self, exercise: FindBugExercise, parent=None) -> None:
        super().__init__(exercise, parent)
        self.lines = QListWidget()
        self.lines.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
            if exercise.allow_multiple
            else QAbstractItemView.SelectionMode.SingleSelection
        )
        for number, line in enumerate(exercise.lines, start=1):
            self.lines.addItem(QListWidgetItem(f"{number:>3}  {line}"))
        self.explanation = QLineEdit()
        self.explanation.setPlaceholderText("Optional: Warum ist diese Zeile auffällig?")
        self.layout.addWidget(self.lines)
        self.layout.addWidget(self.explanation)
        self.finish_layout()

    def answers(self) -> Submission:
        selected = [self.lines.row(item) + 1 for item in self.lines.selectedItems()]
        return Submission(
            exercise_id=self.exercise.id,
            answers={"lines": selected},
            explanation=self.explanation.text() or None,
        )
