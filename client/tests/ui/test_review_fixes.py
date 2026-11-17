"""Regression tests for fixes from the TODO_CLAUDE review."""

from __future__ import annotations

from learnharness_protocol import (
    Blank,
    FillBlanksExercise,
    HealthStatus,
    ReviewItem,
    ReviewResult,
)
from pytestqt.qtbot import QtBot

from learnharness_client.net.fake_tutor_client import FakeTutorClient
from learnharness_client.ui.editor.code_editor import CodeEditor
from learnharness_client.ui.exercises.fill_blanks import FillBlanksWidget, _mark_blanks


def test_failed_health_check_is_a_status_not_an_error(qtbot: QtBot) -> None:
    client = FakeTutorClient(delay_ms=1)
    client.simulate_failure = True
    errors: list[object] = []
    client.error.connect(errors.append)
    with qtbot.waitSignal(client.health_changed, timeout=1000) as signal:
        client.check_health()
    health = signal.args[0]
    assert isinstance(health, HealthStatus)
    assert not health.server_ok
    assert errors == []


def test_agent_code_replacement_is_undoable(qtbot: QtBot) -> None:
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("extends Node\n")
    editor.replace_all_text("extends Node2D\n")
    assert editor.toPlainText() == "extends Node2D\n"
    editor.undo()
    assert editor.toPlainText() == "extends Node\n"


def test_matching_bracket() -> None:
    text = "foo(bar[1], {x})"
    assert CodeEditor._matching_bracket(text, 3) == len(text) - 1
    assert CodeEditor._matching_bracket(text, 7) == 9
    assert CodeEditor._matching_bracket("(", 0) is None


def test_blanks_are_shown_as_numbered_gaps() -> None:
    assert _mark_blanks("position.{{a}} += {{b}}") == "position.[ 1 ] += [ 2 ]"


def test_review_marks_items_and_locks_after_success(qtbot: QtBot) -> None:
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
    widget._submit()
    assert not widget.submit_button.isEnabled()
    widget.show_result(
        ReviewResult(
            correct=False, feedback="Fast.", per_item=[ReviewItem(id="blank_1", correct=False)]
        )
    )
    assert widget.inputs["blank_1"].property("mark") == "wrong"
    assert widget.submit_button.isEnabled()
    widget.show_result(
        ReviewResult(
            correct=True, feedback="Gut!", per_item=[ReviewItem(id="blank_1", correct=True)]
        )
    )
    assert widget.inputs["blank_1"].property("mark") == "correct"
    assert not widget.submit_button.isEnabled()
