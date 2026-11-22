"""Helpers of the exercise widget tests."""

from __future__ import annotations

from learnharness_protocol import Blank, FillBlanksExercise, Submission
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot

from learnharness_client.ui.exercises.base import ExerciseWidget


def _next_focusable(widget: QWidget) -> QWidget:
    """The widget Tab moves to (labels inside the code are skipped)."""
    current = widget.nextInFocusChain()
    while current.focusPolicy() == Qt.FocusPolicy.NoFocus:
        current = current.nextInFocusChain()
    return current


def _emitted(qtbot: QtBot, widget: ExerciseWidget) -> Submission:
    with qtbot.waitSignal(widget.submitted, timeout=1000) as signal:
        widget.submit_button.click()
    submission = signal.args[0]
    assert isinstance(submission, Submission)
    return submission


def _fill() -> FillBlanksExercise:
    return FillBlanksExercise(
        id="fill",
        skill="Bewegung",
        difficulty=1,
        prompt="Ergänze.",
        code="func _process(delta):\n\tposition.{{axis}} += {{speed}} * delta",
        blanks=[Blank(id="speed", options=["speed", "10"]), Blank(id="axis", options=["x", "y"])],
    )
