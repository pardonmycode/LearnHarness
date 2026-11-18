"""Free-text code blanks used from learning level four onward."""

from __future__ import annotations

from learnharness_protocol import Submission, TextBlanksExercise
from PyQt6.QtWidgets import QLineEdit, QWidget

from ..theme import monospace_font
from .base import ExerciseWidget, chain_tab_order, inline_blanks_view
from .fill_blanks import _mark_blanks, numbered_ids


class TextBlanksWidget(ExerciseWidget):
    def __init__(self, exercise: TextBlanksExercise, parent=None) -> None:
        super().__init__(exercise, parent)
        blanks = {blank.id: blank for blank in exercise.blanks}
        self.inputs: dict[str, QLineEdit] = {}
        for index, blank_id in enumerate(numbered_ids(exercise.code, list(blanks)), start=1):
            field = QLineEdit()
            field.setFont(monospace_font())
            field.setPlaceholderText(blanks[blank_id].placeholder)
            field.setMinimumWidth(field.fontMetrics().horizontalAdvance("M") * 10)
            field.setMaxLength(200)
            field.setAccessibleName(f"Lücke {index}")
            field.setToolTip(f"Lücke {index}")
            self.inputs[blank_id] = field
        self.layout.addWidget(
            inline_blanks_view(
                exercise.code,
                dict(self.inputs),
                accessible_name=f"Code mit freien Textlücken: {_mark_blanks(exercise.code)}",
            )
        )
        self.finish_layout()
        chain_tab_order(list(self.inputs.values()), self.submit_button)

    def item_widgets(self) -> dict[str, QWidget]:
        return dict(self.inputs)

    def answers(self) -> Submission:
        return Submission(
            exercise_id=self.exercise.id,
            answers={blank_id: field.text().strip() for blank_id, field in self.inputs.items()},
        )
