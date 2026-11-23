"""Mission exercises stay small, do not give the answer away and keep Python runnable."""

from __future__ import annotations

import pytest
from learnharness_protocol import LearningResponse, TextBlank, TextBlanksExercise
from mission_helpers import _answer, _start
from tutor_helpers import ScriptedProvider

from tutor import engine, harness
from tutor.models import AiSettings, TutorSession


def _exercise(prompt: str = "Was fehlt?", code: str = "for i in {{b1}}:") -> TextBlanksExercise:
    return TextBlanksExercise(
        id="x",
        skill="Schleifen",
        difficulty=3,
        prompt=prompt,
        code=code,
        blanks=[TextBlank(id="b1")],
    )


@pytest.mark.parametrize(
    ("prompt", "message", "clear"),
    [
        ("Was fehlt?", "Los", True),
        ("Nutze range(5).", "Los", False),
        ("Was fehlt?", "Tipp: range( 5 )", False),
    ],
)
def test_task_must_not_give_the_answer_away(prompt: str, message: str, clear: bool) -> None:
    reason = harness.check_blanks_are_clear(_exercise(prompt), {"b1": ["range(5)"]}, message)
    assert (reason is None) is clear


def test_a_plain_name_may_be_part_of_the_task() -> None:
    exercise = _exercise("Erhöhe muenzen um 1.", "{{b1}} += 1")
    assert harness.check_blanks_are_clear(exercise, {"b1": ["muenzen"]}) is None


def test_exercise_code_stays_small() -> None:
    long_code = "\n".join(f"a{n} = {n}" for n in range(6)) + "\nfor i in {{b1}}:"
    assert "Zeilen" in harness.check_blanks_are_clear(_exercise(code=long_code), {"b1": ["x"]})


def test_python_syntax_check() -> None:
    assert harness.check_python_syntax("x = 1\n", "x = 1\ny = 2\n") is None
    assert "Syntaxfehler" in harness.check_python_syntax("x = 1\n", "x = 1\nfor i in:\n")
    assert harness.check_python_syntax("x = (\n", "x = (\ny = 2\n") is None


@pytest.mark.django_db
def test_broken_python_gets_a_second_try(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    from learnharness_protocol import Mission

    session.child.set_skill("loops", "Schleifen", 3)
    message = _start(session)
    mission = Mission.model_validate(session.wish_missions["wunsch-1"])
    mission.steps[0].kind = "exercise"
    session.wish_missions = {mission.id: mission.model_dump(mode="json")}
    session.save(update_fields=["wish_missions"])
    message = message.model_copy(update={"file": "main.py", "code_excerpt": "muenzen = 0\n"})
    answer = _answer(3) | {"code": "for i in {{1}}:\n    muenzen += 1"}
    broken = answer | {"new_file_content": "muenzen = 0\nfor i in range(5)\n    muenzen += 1\n"}
    good = answer | {"new_file_content": "muenzen = 0\nfor i in range(5):\n    muenzen += 1\n"}
    scripted["provider"] = ScriptedProvider(json_answers=[broken, good])
    response = engine.Tutor(session).handle(message)
    assert isinstance(response, LearningResponse) and response.exercise is not None
    assert "Syntaxfehler" in scripted["provider"].calls[1][1][-1]["content"]


@pytest.mark.django_db
def test_prompt_covers_empty_files_running_code_and_the_skill() -> None:
    system = harness.system_prompt("mission_step", AiSettings.load(), language="python")
    assert "Ist <code> leer" in system and "weiter starten" in system
    for stage in (1, 2, 3):
        text = harness.stage_instructions("loops", stage)
        assert '"skill": "loops"' in text and "höchstens 6 Zeilen" in text and "{max" not in text
