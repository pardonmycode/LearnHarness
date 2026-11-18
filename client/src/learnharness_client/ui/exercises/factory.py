"""Map validated exercise models to safe widgets."""

from __future__ import annotations

from learnharness_protocol import (
    FillBlanksExercise,
    FindBugExercise,
    MultipleChoiceExercise,
    OrderingExercise,
    TextBlanksExercise,
)
from PyQt6.QtWidgets import QLabel, QWidget

from ...texts import T
from .fill_blanks import FillBlanksWidget
from .find_bug import FindBugWidget
from .multiple_choice import MultipleChoiceWidget
from .ordering import OrderingWidget
from .text_blanks import TextBlanksWidget


def create_exercise_widget(exercise, parent=None) -> QWidget:
    if isinstance(exercise, FillBlanksExercise):
        return FillBlanksWidget(exercise, parent)
    if isinstance(exercise, MultipleChoiceExercise):
        return MultipleChoiceWidget(exercise, parent)
    if isinstance(exercise, OrderingExercise):
        return OrderingWidget(exercise, parent)
    if isinstance(exercise, FindBugExercise):
        return FindBugWidget(exercise, parent)
    if isinstance(exercise, TextBlanksExercise):
        return TextBlanksWidget(exercise, parent)
    return QLabel(T.EXERCISE_UNKNOWN, parent)
