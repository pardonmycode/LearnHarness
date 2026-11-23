"""The code released after a mission exercise matches the exercise and the child."""

from __future__ import annotations

from typing import Any

import pytest
from learnharness_protocol import (
    Mission,
    StudentMessage,
    Submission,
    TextBlanksExercise,
)
from mission_helpers import _answer, _start
from tutor_helpers import ScriptedProvider

from tutor import engine, harness
from tutor.models import AiSettings, TutorSession

pytestmark = pytest.mark.django_db


def _code_step(session: TutorSession) -> StudentMessage:
    message = _start(session)
    mission = Mission.model_validate(session.wish_missions["wunsch-1"])
    mission.steps[0].kind = "exercise"
    session.wish_missions = {mission.id: mission.model_dump(mode="json")}
    session.save(update_fields=["wish_missions"])
    return message.model_copy(update={"file": "main.py", "code_excerpt": "muenzen = 0\n"})


def _typed_code(new_file: str) -> dict[str, Any]:
    return _answer(3) | {
        "code": "for i in {{1}}:\n    muenzen += 1",
        "blanks": [{"answer": "range(5)", "alternatives": ["range(0, 5)"]}],
        "new_file_content": new_file,
    }


GOOD_FILE = "muenzen = 0\n# Zaehlt fuenf Muenzen\nfor i in range(5):\n    muenzen += 1\n"


def test_released_code_uses_the_childs_own_spelling(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    session.child.set_skill("loops", "Schleifen", 3)
    scripted["provider"] = ScriptedProvider(json_answers=[_typed_code(GOOD_FILE)])
    tutor = engine.Tutor(session)
    exercise = tutor.handle(_code_step(session)).exercise
    review = tutor.review_submission(
        Submission(exercise_id=exercise.id, answers={"b1": "range(0, 5)"})
    )
    assert review.correct is True
    assert "for i in range(0, 5):\n" in review.generated_files[0].content
    assert "# Zaehlt fuenf Muenzen" in review.generated_files[0].content


def test_code_that_does_not_match_the_exercise_is_rejected(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    session.child.set_skill("loops", "Schleifen", 3)
    other = "muenzen = 0\nprint(muenzen)\n"
    scripted["provider"] = ScriptedProvider(
        json_answers=[_typed_code(other), _typed_code(GOOD_FILE)]
    )
    response = engine.Tutor(session).handle(_code_step(session))
    assert isinstance(response.exercise, TextBlanksExercise)
    assert len(scripted["provider"].calls) == 2
    assert "passt nicht zur Übung" in scripted["provider"].calls[1][1][-1]["content"]


def test_typed_spelling_only_changes_one_clear_line() -> None:
    code = "x = {{b1}}"
    twice = "x = 1\nx = 1\n"
    expected = {"b1": ["1", "0 + 1"]}
    assert harness.apply_typed_answers(twice, code, expected, {"b1": "0 + 1"}) == twice
    once = "x = 1  # eins\nmax = 10\n"
    assert harness.apply_typed_answers(once, code, expected, {"b1": "0 + 1"}) == (
        "x = 0 + 1  # eins\nmax = 10\n"
    )
    assert harness.apply_typed_answers(once, code, expected, {"b1": "0\n+ 1"}) == once


def test_prompts_bind_the_exercise_to_project_and_hide_the_answer() -> None:
    system = harness.system_prompt("mission_step", AiSettings.load(), language="python")
    assert "Namen aus <code>" in system and "Jede Zeile mit einer Lücke" in system
    assert "verraten die Antwort" in harness.stage_instructions("loops", 1)


def test_snippet_instead_of_the_whole_file_is_rejected(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    session.child.set_skill("loops", "Schleifen", 3)
    before = "muenzen = 0\nleben = 3\nname = 'Fuchs'\nprint(name)\n"
    snippet = "for i in range(5):\n    muenzen += 1\n"
    scripted["provider"] = ScriptedProvider(
        json_answers=[_typed_code(snippet), _typed_code(before + snippet)]
    )
    message = _code_step(session).model_copy(update={"code_excerpt": before})
    response = engine.Tutor(session).handle(message)
    assert isinstance(response.exercise, TextBlanksExercise)
    assert "vorhandene Zeilen" in scripted["provider"].calls[1][1][-1]["content"]


def test_keeping_code_allows_small_real_changes() -> None:
    before = "muenzen = 0\nleben = 3\nprint(muenzen)\nprint(leben)\n"
    assert harness.check_keeps_code(before, before + "muenzen += 1\n") is None
    assert harness.check_keeps_code(before, before.replace("leben = 3", "leben = 5")) is None
    assert harness.check_keeps_code("", "x = 1\n") is None
    assert harness.check_keeps_code("muenzen = 0\n", "ganz_anders()\n") is not None
    assert harness.check_keeps_code(before, "muenzen = 0\n") is not None


def test_step_knows_which_topics_the_child_has_met(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    session.child.set_skill("variables", "Variablen", 2)
    scripted["provider"] = ScriptedProvider(json_answers=[_answer(1)])
    engine.Tutor(session).handle(_start(session))
    prompt = scripted["provider"].calls[0][1][0]["content"]
    assert "kennt das Kind schon: variables, loops." in prompt
    assert "classes" not in prompt
    assert "Nutze nur die einfachsten" in harness.known_topics_note({}, None)


def test_stage_one_only_introduces_the_topic_once() -> None:
    rule = harness.stage_instructions("loops", 1)
    assert "noch kein [x]" in rule and "nur, was in diesem Schritt neu ist" in rule
    system = harness.system_prompt("mission_step", AiSettings.load(), language="python")
    assert "kompletten neuen Inhalt" in system
