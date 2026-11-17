"""Single- or multiple-choice exercise."""

from __future__ import annotations

from learnharness_protocol import MultipleChoiceExercise, Submission
from PyQt6.QtWidgets import QButtonGroup, QCheckBox, QPlainTextEdit, QRadioButton

from .base import ExerciseWidget


class MultipleChoiceWidget(ExerciseWidget):
    def __init__(self, exercise: MultipleChoiceExercise, parent=None) -> None:
        super().__init__(exercise, parent)
        if exercise.code:
            code = QPlainTextEdit(exercise.code)
            code.setReadOnly(True)
            code.setMaximumHeight(100)
            self.layout.addWidget(code)
        self.group = QButtonGroup(self)
        self.group.setExclusive(not exercise.multiple)
        self.buttons = {}
        for choice in exercise.choices:
            button = QCheckBox(choice.text) if exercise.multiple else QRadioButton(choice.text)
            button.setAccessibleName(choice.text)
            self.group.addButton(button)
            self.buttons[choice.id] = button
            self.layout.addWidget(button)
        self.finish_layout()

    def answers(self) -> Submission:
        selected = [choice_id for choice_id, button in self.buttons.items() if button.isChecked()]
        answer: str | list[str] = (
            selected if self.exercise.multiple else (selected[0] if selected else "")
        )
        return Submission(exercise_id=self.exercise.id, answers={"choice": answer})
