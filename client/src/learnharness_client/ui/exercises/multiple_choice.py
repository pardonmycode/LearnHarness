"""Single- or multiple-choice exercise."""

from __future__ import annotations

from learnharness_protocol import MultipleChoiceExercise, Submission
from PyQt6.QtWidgets import QAbstractButton, QButtonGroup, QCheckBox, QRadioButton, QWidget

from .base import ExerciseWidget, code_view


class MultipleChoiceWidget(ExerciseWidget):
    def __init__(self, exercise: MultipleChoiceExercise, parent=None) -> None:
        super().__init__(exercise, parent)
        if exercise.code:
            self.layout.addWidget(code_view(exercise.code, accessible_name="Code zur Frage"))
        self.group = QButtonGroup(self)
        self.group.setExclusive(not exercise.multiple)
        self.buttons: dict[str, QAbstractButton] = {}
        for choice in exercise.choices:
            button = QCheckBox(choice.text) if exercise.multiple else QRadioButton(choice.text)
            button.setAccessibleName(choice.text)
            self.group.addButton(button)
            self.buttons[choice.id] = button
            self.layout.addWidget(button)
        self.finish_layout()

    def item_widgets(self) -> dict[str, QWidget]:
        return dict(self.buttons)

    def answers(self) -> Submission:
        selected = [choice_id for choice_id, button in self.buttons.items() if button.isChecked()]
        answer: str | list[str] = (
            selected if self.exercise.multiple else (selected[0] if selected else "")
        )
        return Submission(exercise_id=self.exercise.id, answers={"choice": answer})
