"""Fill-in-the-blank exercise."""

from __future__ import annotations

from learnharness_protocol import FillBlanksExercise, Submission
from PyQt6.QtWidgets import QComboBox, QFormLayout, QLabel, QPlainTextEdit

from .base import ExerciseWidget


class FillBlanksWidget(ExerciseWidget):
    def __init__(self, exercise: FillBlanksExercise, parent=None) -> None:
        super().__init__(exercise, parent)
        code = QPlainTextEdit(exercise.code)
        code.setReadOnly(True)
        code.setMaximumHeight(110)
        code.setAccessibleName("Code mit Lücken")
        self.layout.addWidget(code)
        form = QFormLayout()
        self.inputs: dict[str, QComboBox] = {}
        for index, blank in enumerate(exercise.blanks, start=1):
            combo = QComboBox()
            combo.addItem("Bitte auswählen …", None)
            for option in blank.options:
                combo.addItem(option, option)
            combo.setAccessibleName(f"Antwort für Lücke {index}")
            self.inputs[blank.id] = combo
            form.addRow(QLabel(f"Lücke {index}:"), combo)
        self.layout.addLayout(form)
        self.finish_layout()

    def answers(self) -> Submission:
        values = {
            blank_id: str(combo.currentData() or "") for blank_id, combo in self.inputs.items()
        }
        return Submission(exercise_id=self.exercise.id, answers=values)
