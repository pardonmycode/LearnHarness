"""Submissions, factory and fill-blank layout."""

from __future__ import annotations

from exercise_helpers import _emitted, _fill, _next_focusable
from learnharness_protocol import (
    Blank,
    Choice,
    FillBlanksExercise,
    FindBugExercise,
    MultipleChoiceExercise,
    OrderingExercise,
    OrderItem,
    ReviewResult,
    TextBlank,
    TextBlanksExercise,
)
from PyQt6.QtWidgets import QFrame
from pytestqt.qtbot import QtBot

from learnharness_client.ui.exercises.base import ExerciseWidget
from learnharness_client.ui.exercises.factory import create_exercise_widget
from learnharness_client.ui.exercises.fill_blanks import FillBlanksWidget
from learnharness_client.ui.exercises.multiple_choice import MultipleChoiceWidget
from learnharness_client.ui.exercises.text_blanks import TextBlanksWidget


def test_fill_blank_submission(qtbot: QtBot) -> None:
    exercise = FillBlanksExercise(
        id="fill",
        skill="Koordinaten",
        difficulty=1,
        prompt="Ergänze.",
        code="position.{{blank_1}} += 10",
        blanks=[Blank(id="blank_1", options=["x", "y"])],
    )
    widget = FillBlanksWidget(exercise)
    qtbot.addWidget(widget)
    widget.inputs["blank_1"].setCurrentIndex(1)
    submission = widget.answers()
    assert submission.answers == {"blank_1": "x"}
    widget.show_result(ReviewResult(correct=True, feedback="Gut!"))
    assert "✓" in widget.result_label.text()


def test_multiple_choice_submission(qtbot: QtBot) -> None:
    exercise = MultipleChoiceExercise(
        id="choice",
        skill="Koordinaten",
        difficulty=1,
        prompt="Welche Achse?",
        choices=[Choice(id="x", text="X"), Choice(id="y", text="Y")],
    )
    widget = MultipleChoiceWidget(exercise)
    qtbot.addWidget(widget)
    widget.buttons["x"].setChecked(True)
    assert widget.answers().answers == {"choice": "x"}


def test_free_text_blanks_submission(qtbot: QtBot) -> None:
    exercise = TextBlanksExercise(
        id="text",
        skill="Koordinaten",
        difficulty=2,
        prompt="Ergänze ohne Auswahl.",
        code="position.{{axis}} += {{value}} * delta",
        blanks=[TextBlank(id="axis"), TextBlank(id="value")],
    )
    widget = TextBlanksWidget(exercise)
    qtbot.addWidget(widget)
    widget.inputs["axis"].setText("x")
    widget.inputs["value"].setText("speed")
    assert widget.answers().answers == {"axis": "x", "value": "speed"}


def test_factory_creates_a_widget_for_every_type(qtbot: QtBot) -> None:
    exercises = [
        _fill(),
        MultipleChoiceExercise(
            id="mc",
            skill="s",
            difficulty=1,
            prompt="?",
            choices=[Choice(id="a", text="A"), Choice(id="b", text="B")],
        ),
        OrderingExercise(
            id="ord",
            skill="s",
            difficulty=1,
            prompt="?",
            items=[OrderItem(id="a", text="A"), OrderItem(id="b", text="B")],
        ),
        FindBugExercise(id="bug", skill="s", difficulty=1, prompt="?", lines=["a", "b"]),
        TextBlanksExercise(
            id="tb", skill="s", difficulty=1, prompt="?", code="{{a}}", blanks=[TextBlank(id="a")]
        ),
    ]
    for exercise in exercises:
        widget = create_exercise_widget(exercise)
        qtbot.addWidget(widget)
        assert isinstance(widget, ExerciseWidget), exercise.kind


def test_fill_blanks_are_embedded_inline_in_reading_order(qtbot: QtBot) -> None:
    widget = FillBlanksWidget(_fill())
    qtbot.addWidget(widget)
    # Numbering follows the code, not the order of the blank list.
    assert list(widget.inputs) == ["axis", "speed"]
    assert widget.inputs["axis"].accessibleName() == "Lücke 1"
    assert widget.inputs["speed"].accessibleName() == "Lücke 2"
    code_frame = widget.findChild(QFrame, "inlineCode")
    assert code_frame is not None
    assert code_frame.isAncestorOf(widget.inputs["axis"])
    assert code_frame.isAncestorOf(widget.inputs["speed"])
    assert _next_focusable(widget.inputs["axis"]) is widget.inputs["speed"]
    assert _next_focusable(widget.inputs["speed"]) is widget.submit_button
    widget.inputs["axis"].setCurrentIndex(widget.inputs["axis"].findData("x"))
    widget.inputs["speed"].setCurrentIndex(widget.inputs["speed"].findData("speed"))
    submission = _emitted(qtbot, widget)
    assert submission.exercise_id == "fill"
    assert submission.answers == {"axis": "x", "speed": "speed"}


def test_fill_blanks_unanswered_gap_is_sent_empty(qtbot: QtBot) -> None:
    widget = FillBlanksWidget(_fill())
    qtbot.addWidget(widget)
    assert _emitted(qtbot, widget).answers == {"axis": "", "speed": ""}


def test_blank_missing_from_code_is_still_reachable(qtbot: QtBot) -> None:
    exercise = TextBlanksExercise(
        id="tb",
        skill="s",
        difficulty=1,
        prompt="?",
        code="var speed = {{value}}",
        blanks=[TextBlank(id="value"), TextBlank(id="extra")],
    )
    widget = TextBlanksWidget(exercise)
    qtbot.addWidget(widget)
    code_frame = widget.findChild(QFrame, "inlineCode")
    assert code_frame is not None
    assert code_frame.isAncestorOf(widget.inputs["extra"])
    assert widget.inputs["extra"].accessibleName() == "Lücke 2"
