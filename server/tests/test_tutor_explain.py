"""The tab "Code verstehen" explains openly and asks a question that cannot be copied."""

from __future__ import annotations

from typing import Any

import pytest
from learnharness_protocol import LearningResponse, MultipleChoiceExercise, StudentMessage
from tutor_helpers import ScriptedProvider

from tutor import engine, harness
from tutor.models import AiSettings, ExerciseRecord, TutorSession

RIGHT = "Die Schleife läuft dreimal"


def _answer(**changes: Any) -> dict[str, Any]:
    return {
        "message": "range(5) zählt von 0 bis 4, wie fünf Stufen auf einer Treppe.",
        "skill": "loops",
        "kind": "multiple_choice",
        "prompt": "Was passiert mit range(3)?",
        "code": "for i in range(3):",
        "choices": [{"text": RIGHT, "correct": True}, {"text": "Gar nichts", "correct": False}],
        "explanation_after_correct": "Genau.",
    } | changes


def _message(session: TutorSession) -> StudentMessage:
    return StudentMessage(
        intent="explain",
        language="python",
        session_id=session.id,
        project_id="spiel",
        file="main.py",
        code_excerpt="for i in range(5):\n    muenzen += 1\n",
        excerpt_start_line=1,
        message="Was macht range?",
    )


@pytest.mark.django_db
def test_explanation_is_kept_and_never_writes_code(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    scripted["provider"] = ScriptedProvider(json_answers=[_answer()])
    response = engine.Tutor(session).handle(_message(session))
    assert isinstance(response, LearningResponse)
    assert response.message.startswith("range(5) zählt")
    assert isinstance(response.exercise, MultipleChoiceExercise)
    assert ExerciseRecord.objects.get(pk=response.exercise.id).generated_content == ""
    system = scripted["provider"].calls[0][0]
    assert "ohne Lösung" not in system and "veränderten Fall" in system


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("bad", "reason"),
    [
        ({"message": "  "}, "Erklärung"),
        ({"kind": "fill_blanks"}, "multiple_choice"),
        ({"message": f"{RIGHT}, weil range(3) drei Zahlen liefert."}, "wörtlich"),
        ({"code": "\n".join(f"a{n} = {n}" for n in range(7))}, "Zeilen"),
    ],
)
def test_bad_explanations_get_a_second_try(
    session: TutorSession,
    scripted: dict[str, ScriptedProvider],
    bad: dict[str, Any],
    reason: str,
) -> None:
    scripted["provider"] = ScriptedProvider(json_answers=[_answer(**bad), _answer()])
    response = engine.Tutor(session).handle(_message(session))
    assert isinstance(response, LearningResponse) and response.exercise is not None
    assert reason in scripted["provider"].calls[1][1][-1]["content"]


def test_short_answers_may_appear_in_the_explanation() -> None:
    built = harness.build_exercise(
        _answer(choices=[{"text": "fünf", "correct": True}, {"text": "drei", "correct": False}]),
        max_lines=3,
        prefix="explain",
        kind="multiple_choice",
    )
    assert harness.check_explanation(built.exercise, built.answers, "Das sind fünf Stufen.") is None


@pytest.mark.django_db
def test_schema_has_no_code_for_the_file() -> None:
    properties = harness.EXPLAIN_SCHEMA["properties"]
    assert "new_file_content" not in properties and "blanks" not in properties
    assert properties["kind"]["enum"] == ["multiple_choice"]
    assert "new_file_content" not in harness.EXPLAIN_FORMAT_HELP
    assert "Auswahlaufgabe" in harness.system_prompt("explain", AiSettings.load())


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("level", "kind"), [(1, "multiple_choice"), (5, "ordering"), (8, "find_bug")]
)
def test_admin_preview_shows_the_real_formats(teacher: Any, level: int, kind: str) -> None:
    response = teacher.get("/ki/prompts/", {"stufe": level})
    page = {item["key"]: item for item in response.context["intents"]}
    assert f'"{kind}"' in page["learn"]["schema"]
    assert "new_file_content" not in page["explain"]["schema"]
    assert "Stufe" in page["mission_step"]["system"]
