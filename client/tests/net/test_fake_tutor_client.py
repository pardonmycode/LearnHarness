from __future__ import annotations

from learnharness_protocol import HealthStatus, StudentMessage, Submission
from pytestqt.qtbot import QtBot

from learnharness_client.net.fake_tutor_client import FakeTutorClient


def test_fake_health_and_stream(qtbot: QtBot) -> None:
    client = FakeTutorClient(delay_ms=1)
    with qtbot.waitSignal(client.health_changed, timeout=1000) as health_signal:
        client.check_health()
    health = health_signal.args[0]
    assert isinstance(health, HealthStatus)
    assert health.model_ok

    message = StudentMessage(
        session_id="session",
        project_id="project",
        message="Wie bewege ich die Figur?",
    )
    chunks: list[str] = []
    client.stream_chunk.connect(chunks.append)
    with qtbot.waitSignal(client.stream_finished, timeout=1500) as response_signal:
        client.send_message(message)
    response = response_signal.args[0]
    assert response.mode == "socratic"
    assert response.code_changes == []
    assert "X oder Y" in "".join(chunks)


def test_fake_session_keeps_pseudonym(qtbot: QtBot) -> None:
    client = FakeTutorClient(delay_ms=1)
    with qtbot.waitSignal(client.session_started, timeout=1000) as session_signal:
        client.start_session("project", "profile-id", "CodeFuchs", 2)
    assert session_signal.args[0].student_pseudonym == "CodeFuchs"


def test_fake_question_adapts_to_experience(qtbot: QtBot) -> None:
    client = FakeTutorClient(delay_ms=1)
    with qtbot.waitSignal(client.session_started, timeout=1000):
        client.start_session("project", "profile-id", "PixelProfi", 3)
    message = StudentMessage(
        session_id="session",
        project_id="project",
        experience_level=3,
        message="Wie bewege ich die Figur?",
    )
    with qtbot.waitSignal(client.stream_finished, timeout=1500) as response_signal:
        client.send_message(message)
    assert "Vector2" in response_signal.args[0].message


def test_learn_agent_writes_code_only_after_correct_answer(qtbot: QtBot) -> None:
    client = FakeTutorClient(delay_ms=1)
    message = StudentMessage(
        session_id="session",
        project_id="project",
        learning_level=1,
        file="player.gd",
        message="Meine Figur soll nach rechts laufen.",
    )
    with qtbot.waitSignal(client.stream_finished, timeout=1000) as response_signal:
        client.send_message(message)
    exercise = response_signal.args[0].exercise
    assert exercise is not None
    assert exercise.kind == "multiple_choice"

    with qtbot.waitSignal(client.review_received, timeout=1000) as wrong_signal:
        client.submit_exercise(
            Submission(exercise_id="learn_level_1", answers={"choice": "y_axis"})
        )
    assert wrong_signal.args[0].correct is False
    assert wrong_signal.args[0].generated_files == []

    with qtbot.waitSignal(client.review_received, timeout=1000) as correct_signal:
        client.submit_exercise(
            Submission(exercise_id="learn_level_1", answers={"choice": "x_axis"})
        )
    review = correct_signal.args[0]
    assert review.correct is True
    assert review.generated_files[0].path == "player.gd"
    assert "extends Node2D" in review.generated_files[0].content


def test_levels_one_to_four_have_requested_exercise_types(qtbot: QtBot) -> None:
    client = FakeTutorClient(delay_ms=1)
    expected = {
        1: "multiple_choice",
        2: "fill_blanks",
        3: "fill_blanks",
        4: "text_blanks",
    }
    for level, kind in expected.items():
        message = StudentMessage(
            session_id="session",
            project_id="project",
            learning_level=level,
            file="player.gd",
            message="Figur bewegen",
        )
        with qtbot.waitSignal(client.stream_finished, timeout=1000) as signal:
            client.send_message(message)
        assert signal.args[0].exercise.kind == kind


def test_fourth_hint_produces_exercise(qtbot: QtBot) -> None:
    client = FakeTutorClient(delay_ms=1)
    for _ in range(3):
        with qtbot.waitSignal(client.stream_finished, timeout=1000):
            client.request_next_hint("task")
    with qtbot.waitSignal(client.exercise_received, timeout=1000) as exercise_signal:
        client.request_next_hint("task")
    exercise = exercise_signal.args[0]
    assert exercise.kind == "fill_blanks"
    assert not hasattr(exercise, "solution")
