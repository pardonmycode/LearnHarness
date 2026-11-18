"""Fill-in-the-blank exercise with the choices embedded directly in the code."""

from __future__ import annotations

from learnharness_protocol import FillBlanksExercise, Submission
from PyQt6.QtWidgets import QComboBox, QWidget

from .base import ExerciseWidget, blank_order, chain_tab_order, inline_blanks_view


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


def numbered_ids(code: str, blank_ids: list[str]) -> list[str]:
    """Blank ids in reading order; blanks missing from the code come last."""
    in_code = [blank_id for blank_id in blank_order(code) if blank_id in blank_ids]
    return in_code + [blank_id for blank_id in blank_ids if blank_id not in in_code]


class FillBlanksWidget(ExerciseWidget):
    def __init__(self, exercise: FillBlanksExercise, parent=None) -> None:
        super().__init__(exercise, parent)
        blanks = {blank.id: blank for blank in exercise.blanks}
        self.inputs: dict[str, QComboBox] = {}
        for index, blank_id in enumerate(numbered_ids(exercise.code, list(blanks)), start=1):
            combo = QComboBox()
            combo.addItem(f"{index}: wählen …", None)
            for option in blanks[blank_id].options:
                combo.addItem(option, option)
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
            combo.setAccessibleName(f"Lücke {index}")
            combo.setToolTip(f"Lücke {index}")
            self.inputs[blank_id] = combo
        self.layout.addWidget(
            inline_blanks_view(
                exercise.code,
                dict(self.inputs),
                accessible_name=f"Code mit Lücken: {_mark_blanks(exercise.code)}",
            )
        )
        self.finish_layout()
        chain_tab_order(list(self.inputs.values()), self.submit_button)

    def item_widgets(self) -> dict[str, QWidget]:
        return dict(self.inputs)

    def answers(self) -> Submission:
        values = {
            blank_id: str(combo.currentData() or "") for blank_id, combo in self.inputs.items()
        }
        return Submission(exercise_id=self.exercise.id, answers=values)
