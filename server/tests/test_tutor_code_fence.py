"""Markdown fences never end up in a child's script."""

from __future__ import annotations

import pytest
from learnharness_protocol import LearningResponse, StudentMessage
from tutor_helpers import PLAYER, ScriptedProvider, _exercise_json

from tutor import engine, harness
from tutor.models import AiSettings, ExerciseRecord, TutorSession

NEW = PLAYER + "# Wie stark die Figur springt\nvar jump_force = 400\n"


def _learn(session: TutorSession) -> StudentMessage:
    return StudentMessage(
        intent="learn",
        session_id=session.id,
        project_id="spiel",
        file="player.gd",
        code_excerpt=PLAYER,
        message="Lass die Figur springen",
    )


def test_unwrap_only_removes_a_fence_around_everything() -> None:
    assert harness.unwrap_code_fence("```python\nx = 1\ny = 2\n```\n") == "x = 1\ny = 2\n"
    assert harness.unwrap_code_fence("```\nx = 1\n```") == "x = 1\n"
    assert harness.unwrap_code_fence("x = 1\n") == "x = 1\n"
    inner = "x = 1\n```\ny = 2\n"
    assert harness.unwrap_code_fence(inner) == inner


def test_stray_fence_is_found_but_the_childs_own_text_is_fine() -> None:
    assert harness.has_stray_fence("x = 1\n```\ny = 2\n", "x = 1\n")
    assert not harness.has_stray_fence("x = 1\n", "")
    own = 'text = """\n```\n"""\n'
    assert not harness.has_stray_fence(own + "y = 2\n", own)


@pytest.mark.django_db
def test_fenced_file_is_stored_without_the_fence(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    fenced = f"```gdscript\n{NEW}```"
    scripted["provider"] = ScriptedProvider(json_answers=[_exercise_json(new_file_content=fenced)])
    response = engine.Tutor(session).handle(_learn(session))
    assert isinstance(response, LearningResponse) and response.exercise is not None
    record = ExerciseRecord.objects.get(pk=response.exercise.id)
    assert "```" not in record.generated_content and "var jump_force" in record.generated_content


@pytest.mark.django_db
def test_fence_inside_the_file_gets_a_second_try(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    broken = PLAYER + "```\nvar jump_force = 400\n"
    scripted["provider"] = ScriptedProvider(
        json_answers=[_exercise_json(new_file_content=broken), _exercise_json()]
    )
    response = engine.Tutor(session).handle(_learn(session))
    assert isinstance(response, LearningResponse) and response.exercise is not None
    assert "Codeblöcke" in scripted["provider"].calls[1][1][-1]["content"]


@pytest.mark.django_db
def test_rules_separate_child_texts_from_file_code() -> None:
    system = harness.system_prompt("mission_step", AiSettings.load(), language="python")
    assert "in deinen Texten keine fertigen" in system
    assert 'Ausnahme von Regel 1 und 2: Die JSON-Felder "code", "ordered_lines"' in system
