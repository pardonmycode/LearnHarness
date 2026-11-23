"""Mission exercises must not mark a right answer as wrong."""

from __future__ import annotations

import pytest
from learnharness_protocol import (
    Blank,
    FillBlanksExercise,
    LearningResponse,
    TextBlank,
    TextBlanksExercise,
)
from mission_helpers import _answer, _start
from tutor_helpers import ScriptedProvider

from tutor import engine, harness
from tutor.models import TutorSession


def _typed(prompt: str, code: str = "muenzen = {{b1}}") -> TextBlanksExercise:
    return TextBlanksExercise(
        id="x",
        skill="Variablen",
        difficulty=3,
        prompt=prompt,
        code=code,
        blanks=[TextBlank(id="b1")],
    )


def _dropdown(options: list[str]) -> FillBlanksExercise:
    return FillBlanksExercise(
        id="x",
        skill="Schleifen",
        difficulty=2,
        prompt="Was fehlt?",
        code="for i in {{b1}}:",
        blanks=[Blank(id="b1", options=options)],
    )


@pytest.mark.parametrize(
    ("prompt", "code", "answer", "clear"),
    [
        ("Setze die Münzen.", "muenzen = {{b1}}", "5", False),
        ("Der Fuchs startet mit 5 Münzen.", "muenzen = {{b1}}", "5", True),
        ("Gib der Figur einen Namen.", "name = {{b1}}", '"Fuchs"', False),
        ("Er heißt Fuchs.", "name = {{b1}}", '"Fuchs"', True),
        ("Er startet mit 5 Münzen.", "var muenzen := {{b1}}  # Start", "5", True),
        ("Setze die Münzen.", "var muenzen := {{b1}}", "5", False),
        ("Erhöhe die Münzen.", "muenzen = {{b1}}", "muenzen + 1", True),
        ("Was fehlt?", "for i in {{b1}}:", "range(5)", True),
    ],
)
def test_free_values_must_be_named(prompt: str, code: str, answer: str, clear: bool) -> None:
    reason = harness.check_blanks_are_clear(_typed(prompt, code), {"b1": [answer]})
    assert (reason is None) is clear


def test_same_solution_twice_in_a_dropdown_is_rejected() -> None:
    assert harness.check_blanks_are_clear(_dropdown(["x+1", "x + 1", "y"]), {"b1": "x+1"})
    assert harness.check_blanks_are_clear(_dropdown(["x+1", "x-1"]), {"b1": "x+1"}) is None


@pytest.mark.django_db
def test_unclear_task_gets_a_second_try(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    session.child.set_skill("loops", "Schleifen", 3)
    unclear = _answer(3) | {
        "prompt": "Setze die Münzen.",
        "code": "muenzen = {{1}}",
        "blanks": [{"answer": "5", "alternatives": []}],
    }
    clear = unclear | {"prompt": "Der Fuchs startet mit 5 Münzen."}
    scripted["provider"] = ScriptedProvider(json_answers=[unclear, clear])
    response = engine.Tutor(session).handle(_start(session))
    assert isinstance(response, LearningResponse) and response.exercise.prompt == clear["prompt"]
    assert "nicht eindeutig" in scripted["provider"].calls[1][1][-1]["content"]


def test_stage_prompts_ask_for_one_clear_solution() -> None:
    assert "Genau eine Option ist richtig" in harness.stage_instructions("loops", 2)
    assert "genau eine Lösung" in harness.stage_instructions("loops", 3)
