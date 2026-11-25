"""Planning a mission in a Godot project: right script, missing scenes and keys."""

from __future__ import annotations

from typing import Any

import pytest
from learnharness_protocol import (
    ErrorMessage,
    LearningResponse,
    SceneContext,
    SceneNode,
    StudentMessage,
)
from tutor_helpers import ScriptedProvider

from tutor import engine, harness
from tutor.models import AiSettings, TutorSession

pytestmark = pytest.mark.django_db

SCENE = SceneContext(
    path="entities/player/player.tscn",
    root_name="Player",
    script_node=".",
    nodes=[SceneNode(path=".", type="CharacterBody2D", script="res://entities/player/player.gd")],
)
FILES = ["main/main.tscn", "entities/player/player.tscn", "main/main.gd", "player.gd"]


def _plan(**overrides: Any) -> dict[str, Any]:
    data = {
        "title": "Schleime tauchen auf",
        "goal": "Alle 2 Sekunden erscheint ein Schleim.",
        "message": "Los geht's!",
        "skill": "variables",
        "steps": [
            {"title": "Was ist ein Timer?", "kind": "understand"},
            {"title": "Timer einbauen", "kind": "exercise"},
        ],
        "open_file": "",
    }
    data.update(overrides)
    return data


def _ask(session: TutorSession, **extra: Any) -> ErrorMessage | LearningResponse:
    message = StudentMessage(
        intent="mission",
        session_id=session.id,
        project_id="spiel",
        file="player.gd",
        scene=SCENE,
        message="Schleime sollen auftauchen",
        **{"project_files": FILES, **extra},
    )
    response = engine.Tutor(session).handle(message)
    assert isinstance(response, ErrorMessage | LearningResponse)
    return response


def test_planner_knows_scenes_files_keys_and_the_signal_exception(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    scripted["provider"] = ScriptedProvider(json_answers=[_plan()])
    response = _ask(session)
    assert isinstance(response, LearningResponse) and response.mission is not None
    system, messages = scripted["provider"].calls[0]
    assert harness.MISSION_FILES_NOTE in system
    for text in (
        '"open_file"',
        "Eingabe-Zuordnung",
        "keinen eigenen Schritt",
        "Gerüst",
        "ist keine Schleife",
    ):
        assert text in system
    assert "<dateien>\nres://main/main.tscn" in messages[0]["content"]


def test_wish_for_another_script_names_it_instead_of_a_plan(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    scripted["provider"] = ScriptedProvider(
        json_answers=[_plan(open_file="res://main/main.gd", steps=[])]
    )
    response = _ask(session)
    assert isinstance(response, ErrorMessage) and response.code == "open_other_file"
    assert "main/main.gd" in response.message_for_child
    assert session.wish_missions == {}


@pytest.mark.parametrize("wrong", ["main/main.tscn", "erfunden.gd", "player.gd", "x.tscn"])
def test_open_file_must_be_another_existing_script(
    session: TutorSession, scripted: dict[str, ScriptedProvider], wrong: str
) -> None:
    scripted["provider"] = ScriptedProvider(json_answers=[_plan(open_file=wrong), _plan()])
    response = _ask(session)
    assert isinstance(response, LearningResponse) and response.mission is not None
    retry = scripted["provider"].calls[1][1][-1]["content"]
    assert '"open_file"' in retry


def test_python_missions_have_no_scene_rules() -> None:
    settings = AiSettings.load()
    assert harness.MISSION_FILES_NOTE not in harness.system_prompt(
        "mission", settings, language="python"
    )
    assert "open_file" not in harness.mission_schema(["variables"])["properties"]


def test_scene_without_a_script_asks_the_child_to_attach_one(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    scripted["provider"] = ScriptedProvider(json_answers=[_plan(open_file="levels/level_01.tscn")])
    response = _ask(session, project_files=[*FILES, "levels/level_01.tscn"])
    assert isinstance(response, ErrorMessage) and response.code == "open_other_file"
    assert "levels/level_01.tscn" in response.message_for_child
    assert "Skript anhängen" in response.message_for_child


def test_planner_gets_one_rule_for_other_files_and_room_for_two_sentences() -> None:
    system = harness.system_prompt("mission", AiSettings.load(), language="gdscript")
    assert "ein bis zwei kurze, motivierende Sätze" in system
    assert "Gehört nur ein Teil des Bausteins" in system
    assert "Gehört der ganze Wunsch oder der ganze nächste Baustein" in system
