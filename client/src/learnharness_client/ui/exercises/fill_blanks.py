"""Fill-in-the-blank exercise."""

from __future__ import annotations

from learnharness_protocol import FillBlanksExercise, Submission
from PyQt6.QtWidgets import QComboBox, QFormLayout, QLabel, QWidget

from .base import ExerciseWidget, code_view


def _mark_blanks(code: str) -> str:
    """Show {{blank_id}} placeholders as numbered gaps: [ 1 ], [ 2 ] …"""
    result = code
    index = 1
    while "{{" in result and "}}" in result:
        start = result.index("{{")
        end = result.index("}}", start)
        result = f"{result[:start]}[ {index} ]{result[end + 2 :]}"
        index += 1
    return result


class FillBlanksWidget(ExerciseWidget):
    def __init__(self, exercise: FillBlanksExercise, parent=None) -> None:
        super().__init__(exercise, parent)
        self.layout.addWidget(
            code_view(_mark_blanks(exercise.code), accessible_name="Code mit Lücken")
        )
        form = QFormLayout()
        self.inputs: dict[str, QComboBox] = {}
        for index, blank in enumerate(exercise.blanks, start=1):
            combo = QComboBox()
            combo.addItem("Bitte auswählen …", None)
            for option in blank.options:
                combo.addItem(option, option)
            combo.setAccessibleName(f"Antwort für Lücke {index}")
            self.inputs[blank.id] = combo
            form.addRow(QLabel(f"Lücke {index}"), combo)
        self.layout.addLayout(form)
        self.finish_layout()

    def item_widgets(self) -> dict[str, QWidget]:
        return dict(self.inputs)

    def answers(self) -> Submission:
        values = {
            blank_id: str(combo.currentData() or "") for blank_id, combo in self.inputs.items()
        }
        return Submission(exercise_id=self.exercise.id, answers=values)
