"""The offline helper uses the same kind of exercise per level as the learning server."""

from __future__ import annotations

from typing import Any

import pytest
from learnharness_protocol import StudentMessage, Submission
from pytestqt.qtbot import QtBot

from learnharness_client.net.fake_tutor_client import FakeTutorClient
from learnharness_client.net.fake_tutor_client.level_content import level_answers

KINDS = {
    1: "multiple_choice",
    2: "multiple_choice",
    3: "fill_blanks",
    4: "fill_blanks",
    5: "ordering",
    6: "text_blanks",
    7: "text_blanks",
    8: "find_bug",
    9: "find_bug",
    10: "find_bug",
}
LANGUAGES = {"godot": ("gdscript", "player.gd"), "python": ("python", "main.py")}


def _wrong(answers: dict[str, Any]) -> dict[str, Any]:
    wrong: dict[str, Any] = {}
    for key, value in answers.items():
        wrong[key] = [*reversed(value)] if key == "order" else [1] if key == "lines" else "falsch"
    if "lines" in answers and answers["lines"] == [1]:
        wrong["lines"] = [2]
    return wrong


@pytest.mark.parametrize("name", LANGUAGES)
@pytest.mark.parametrize("level", KINDS)
def test_level_kind_and_answers(qtbot: QtBot, name: str, level: int) -> None:
    language, file = LANGUAGES[name]
    client = FakeTutorClient(delay_ms=1)
    message = StudentMessage(
        language=language,
        session_id="s",
        project_id="p",
        learning_level=level,
        file=file,
        message="Bau etwas",
    )
    with qtbot.waitSignal(client.stream_finished, timeout=1000) as answer:
        client.send_message(message)
    exercise = answer.args[0].exercise
    assert exercise.kind == KINDS[level]
    right = level_answers(name, level)
    with qtbot.waitSignal(client.review_received, timeout=1000) as wrong_review:
        client.submit_exercise(Submission(exercise_id=exercise.id, answers=_wrong(right)))
    assert wrong_review.args[0].correct is False and not wrong_review.args[0].generated_files
    with qtbot.waitSignal(client.review_received, timeout=1000) as right_review:
        client.submit_exercise(Submission(exercise_id=exercise.id, answers=right))
    assert right_review.args[0].correct is True
    assert right_review.args[0].generated_files[0].path == file


@pytest.mark.parametrize("focus_level, kind", [(1, "multiple_choice"), (3, "fill_blanks")])
def test_practice_focus_keeps_the_level_kind(qtbot: QtBot, focus_level: int, kind: str) -> None:
    client = FakeTutorClient(delay_ms=1)
    message = StudentMessage(
        session_id="s",
        project_id="p",
        learning_level=focus_level,
        file="player.gd",
        skill_focus="conditions",
        message="Bau etwas",
    )
    with qtbot.waitSignal(client.stream_finished, timeout=1000) as answer:
        client.send_message(message)
    assert answer.args[0].exercise.kind == kind
