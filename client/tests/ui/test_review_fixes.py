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


def test_agent_may_only_write_the_round_target() -> None:
    from types import SimpleNamespace

    from learnharness_client.ui.main_window import MainWindow

    window = SimpleNamespace(_learn_target_file="scripts/player.gd")
    assert MainWindow._is_learn_target(window, "scripts/player.gd")  # type: ignore[arg-type]
    # Backslashes count as separators everywhere; case rules: see test_platform_paths.py.
    assert MainWindow._is_learn_target(window, r".\scripts\player.gd")  # type: ignore[arg-type]
    assert not MainWindow._is_learn_target(window, "scripts/enemy.gd")  # type: ignore[arg-type]
    window._learn_target_file = None
    assert not MainWindow._is_learn_target(window, "scripts/player.gd")  # type: ignore[arg-type]


def test_offline_pauses_sending_but_keeps_input(qtbot: QtBot) -> None:
    from learnharness_client.ui.panels.learn_agent_panel import LearnAgentPanel
    from learnharness_client.ui.panels.tutor_panel import TutorPanel

    tutor = TutorPanel()
    agent = LearnAgentPanel(max_unlocked_level=1)
    qtbot.addWidget(tutor)
    qtbot.addWidget(agent)
    tutor.input.setPlainText("Wie bewege ich die Figur?")
    tutor.set_available(False)
    agent.set_available(False)
    assert not tutor.send_button.isEnabled()
    assert not agent.start_button.isEnabled()
    tutor._submit()
    assert tutor.input.toPlainText() == "Wie bewege ich die Figur?"
    tutor.set_available(True)
    agent.set_available(True)
    assert tutor.send_button.isEnabled()
    assert agent.start_button.isEnabled()
