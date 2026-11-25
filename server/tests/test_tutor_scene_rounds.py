"""Scene changes travel with an exercise and go out only after a correct answer."""

from __future__ import annotations

from typing import Any

import pytest
from django.test import Client
from learnharness_protocol import (
    LearningResponse,
    ReviewResult,
    SceneContext,
    SceneNode,
    StudentMessage,
)
from tutor_helpers import PLAYER, ScriptedProvider, _exercise_json, _headers

from tutor import engine, harness
from tutor.models import ExerciseRecord, TutorSession

pytestmark = pytest.mark.django_db

SCENE = SceneContext(
    path="player/player.tscn",
    root_name="Player",
    script_node=".",
    nodes=[
        SceneNode(path=".", type="CharacterBody2D", script="res://player/player.gd"),
        SceneNode(path="Sprite2D", type="Sprite2D", properties={"position": "Vector2(0, 0)"}),
    ],
)
TIMER_CODE = PLAYER + (
    "# Wie stark die Figur springt\nvar jump_force = 400\n\n"
    "# Läuft ab, wenn der Timer fertig ist\nfunc _on_timer_timeout():\n\tpass\n"
)


def _entry(op: str, **fields: str) -> dict[str, str]:
    keys = ("parent", "name", "type", "node", "property", "value", "signal", "from", "to")
    return {"op": op, **dict.fromkeys(keys, ""), "method": "", **fields}


TIMER_CHANGES = [
    _entry("add_node", parent=".", name="Timer", type="Timer"),
    _entry("set_property", node="Timer", property="wait_time", value="2.0"),
    _entry("set_property", node="Timer", property="autostart", value="true"),
    _entry("connect", signal="timeout", **{"from": "Timer", "to": "."}, method="_on_timer_timeout"),
]


def _learn(session: TutorSession, **extra: Any) -> LearningResponse:
    message = StudentMessage(
        intent="learn",
        session_id=session.id,
        project_id="spiel",
        learning_level=3,
        file="player/player.gd",
        code_excerpt=PLAYER,
        excerpt_start_line=1,
        message="Alle 2 Sekunden soll etwas passieren",
        **extra,
    )
    response = engine.Tutor(session).handle(message)
    assert isinstance(response, LearningResponse) and response.exercise is not None
    return response


def _submit(client: Client, token: str, session: TutorSession, exercise_id: str, answer: str):
    result = client.post(
        f"/api/v1/exercises/{exercise_id}/submissions",
        {"exercise_id": exercise_id, "session_id": session.id, "answers": {"b1": answer}},
        content_type="application/json",
        **_headers(token),
    )
    return ReviewResult.model_validate(result.json())


def test_scene_changes_are_previewed_and_released_after_the_right_answer(
    client: Client, token: str, session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    answer = _exercise_json(new_file_content=TIMER_CODE, scene_changes=TIMER_CHANGES)
    scripted["provider"] = ScriptedProvider(json_answers=[answer])
    response = _learn(
        session, scene=SCENE, input_actions=["springen"], project_files=["player/player.tscn"]
    )
    system, messages = scripted["provider"].calls[0]
    prompt = messages[0]["content"]
    assert '"scene_changes"' in system and "<szene>" in prompt and "springen" in prompt
    assert "Sprite2D (Sprite2D) {position = Vector2(0, 0)}" in prompt
    assert "- Player (Wurzel) (CharacterBody2D) ← Skript" in prompt
    assert "<dateien>\nres://player/player.tscn\n</dateien>" in prompt
    assert "Instanz" in system and "Hauptszene" in system and "nur über" in system
    assert "Ausnahme von den Themen" in system and "autostart" in system
    assert 'nie in "scene_changes"' in system
    assert response.scene_preview is not None
    assert [change.op for change in response.scene_preview.changes] == [
        "add_node",
        "set_property",
        "set_property",
        "connect",
    ]
    assert response.exercise is not None
    wrong = _submit(client, token, session, response.exercise.id, "func")
    assert wrong.correct is False and wrong.scene_edits == []
    right = _submit(client, token, session, response.exercise.id, "var")
    assert right.correct is True and right.generated_files
    edit = right.scene_edits[0]
    assert edit.path == "player/player.tscn" and len(edit.changes) == 4


def test_code_with_a_missing_node_is_retried(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    broken = _exercise_json(
        new_file_content=PLAYER
        + "# Wie stark die Figur springt\nvar jump_force = 400\n\n"
        + "# Startet den Timer\nfunc _ready():\n\t$Timer.start()\n",
        scene_changes=[],
    )
    fixed = _exercise_json(new_file_content=TIMER_CODE, scene_changes=TIMER_CHANGES)
    scripted["provider"] = ScriptedProvider(json_answers=[broken, fixed])
    response = _learn(session, scene=SCENE)
    retry = scripted["provider"].calls[1][1]
    assert "Knoten Timer gibt es in der Szene nicht" in retry[-1]["content"]
    assert response.scene_preview is not None


def test_without_a_scene_nothing_in_the_scene_changes(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    scripted["provider"] = ScriptedProvider(json_answers=[_exercise_json()])
    response = _learn(session, input_actions=[])
    system = scripted["provider"].calls[0][0]
    assert "keine Szene bekannt" in system and response.scene_preview is None
    record = ExerciseRecord.objects.get()
    assert record.scene_changes == [] and record.scene_path == ""


def test_python_projects_get_no_scene_help(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    python_code = "speed = 200\n"
    answer = _exercise_json(
        new_file_content=python_code + "# Wie stark die Figur springt\njump_force = 400\n",
        code="{{1}} = 400",
        blanks=[{"options": ["jump_force", "def", "if"], "answer": "jump_force"}],
    )
    scripted["provider"] = ScriptedProvider(json_answers=[answer])
    message = StudentMessage(
        intent="learn",
        language="python",
        session_id=session.id,
        project_id="rechner",
        learning_level=3,
        file="main.py",
        code_excerpt=python_code,
        excerpt_start_line=1,
        message="Springen",
    )
    engine.Tutor(session).handle(message)
    assert "Szene" not in scripted["provider"].calls[0][0]


def test_code_that_loads_a_missing_scene_is_retried(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    loads_slime = _exercise_json(
        new_file_content=PLAYER
        + "# Wie stark die Figur springt\nvar jump_force = 400\n"
        + '# Die Schleim-Szene\nvar slime = preload("res://slime.tscn")\n',
    )
    scripted["provider"] = ScriptedProvider(json_answers=[loads_slime, _exercise_json()])
    _learn(session, scene=SCENE, project_files=["player/player.tscn"])
    retry = scripted["provider"].calls[1][1]
    assert "res://slime.tscn gibt es im Projekt nicht" in retry[-1]["content"]


def test_step_without_code_promises_no_scene_change(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    from children.models import LearningMission, LearningMissionStep

    mission = LearningMission.objects.create(mission_id="timer", title="Timer", goal="Warten")
    LearningMissionStep.objects.create(mission=mission, step_id="s1", title="Was?", kind="learn")
    choice = _exercise_json(
        kind="multiple_choice",
        code="",
        blanks=[],
        choices=[{"text": "var", "correct": True}, {"text": "if", "correct": False}],
    )
    scripted["provider"] = ScriptedProvider(json_answers=[choice])
    message = StudentMessage(
        intent="mission_step",
        session_id=session.id,
        project_id="spiel",
        file="player/player.gd",
        code_excerpt=PLAYER,
        scene=SCENE,
        mission_id="timer",
        mission_step_id="s1",
        message="s1",
    )
    response = engine.Tutor(session).handle(message)
    assert isinstance(response, LearningResponse) and response.scene_preview is None
    system = scripted["provider"].calls[0][0]
    assert harness.NO_CODE_STEP_NOTE in system and '"scene_changes" (höchstens' not in system
