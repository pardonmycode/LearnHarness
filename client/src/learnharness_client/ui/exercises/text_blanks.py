"""Free-text code blanks used from learning level four onward."""

from __future__ import annotations

from learnharness_protocol import Submission, TextBlanksExercise
from PyQt6.QtWidgets import QFormLayout, QLabel, QLineEdit, QPlainTextEdit

from .base import ExerciseWidget


class TextBlanksWidget(ExerciseWidget):
    def __init__(self, exercise: TextBlanksExercise, parent=None) -> None:
        super().__init__(exercise, parent)
        code = QPlainTextEdit(exercise.code)
        code.setReadOnly(True)
        code.setMaximumHeight(150)
        code.setAccessibleName("Code mit freien Textlücken")
        self.layout.addWidget(code)
        form = QFormLayout()
        self.inputs: dict[str, QLineEdit] = {}
        for index, blank in enumerate(exercise.blanks, start=1):
            field = QLineEdit()
            field.setPlaceholderText(blank.placeholder)
            field.setAccessibleName(f"Freie Antwort für Lücke {index}")
            self.inputs[blank.id] = field
            form.addRow(QLabel(f"Lücke {index}:"), field)
        self.layout.addLayout(form)
        self.finish_layout()

    def answers(self) -> Submission:
        return Submission(
            exercise_id=self.exercise.id,
            answers={blank_id: field.text().strip() for blank_id, field in self.inputs.items()},
        )
