"""Code review in a Godot project: sure findings from the app, checked against the scene."""

from __future__ import annotations

import pytest
from learnharness_protocol import (
    LearningResponse,
    SceneConnection,
    SceneContext,
    SceneNode,
    StudentMessage,
)
from tutor_helpers import ScriptedProvider

from tutor import engine, harness
from tutor.models import TutorSession

pytestmark = pytest.mark.django_db

SCENE = SceneContext(
    path="main/main.tscn",
    root_name="Main",
    script_node=".",
    nodes=[
        SceneNode(path=".", type="Node2D", script="res://main/main.gd"),
        SceneNode(path="Player", instance="res://entities/player/player.tscn"),
        SceneNode(path="SpawnTimer", type="Timer", properties={"wait_time": "2.0"}),
        SceneNode(path="SpawnPoint", type="Marker2D"),
    ],
    connections=[
        SceneConnection(
            signal="timeout", from_node="SpawnTimer", to_node=".", method="_on_spawn_timer_timeout"
        ),
        SceneConnection(signal="ready", from_node="Player", to_node=".", method="_on_ready"),
    ],
)
FILES = ["main/main.tscn", "entities/enemies/slime/slime.tscn", "main/main.gd"]
CODE = (
    "extends Node2D\n"
    'var slime_scene = preload("res://entities/enemies/slime.tscn")\n'
    "func _on_spawn_timer_timeout():\n"
    "\tvar slime = slime_scene.instantiate()\n"
    "\tslime.position = $SpawnPoint.position\n"
    '\tif Input.is_action_pressed("pause"):  # $Missing only in a comment\n'
    "\t\t$Spawnpunkt.show()\n"
)


def test_findings_name_lines_and_scene_problems() -> None:
    found = harness.scene_findings(SCENE, ["springen"], FILES, CODE)
    assert found == [
        ("Datei res://entities/enemies/slime.tscn gibt es im Projekt nicht", 2),
        ("Input-Aktion „pause“ gibt es im Projekt nicht", 6),
        ("Knoten Spawnpunkt gibt es in der Szene nicht", 7),
        ("Signal Player.ready führt zu _on_ready(), die fehlt", None),
        ("Timer SpawnTimer startet in diesem Skript nicht, und autostart ist aus", None),
    ]


def test_started_or_autostarting_timers_are_fine() -> None:
    started = CODE + "func _ready():\n\t$SpawnTimer.start()\n"
    assert not any("Timer" in text for text, _ in harness.scene_findings(SCENE, [], [], started))
    auto = SCENE.model_copy(deep=True)
    auto.nodes[2].properties["autostart"] = "true"
    assert not any("Timer" in text for text, _ in harness.scene_findings(auto, [], [], CODE))


def test_review_hands_findings_to_the_ai_and_marks_their_lines(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    scripted["provider"] = ScriptedProvider(
        json_answers=[{"feedback": "Schön aufgeteilt! Schau dir den Pfad an.", "marked_lines": []}]
    )
    message = StudentMessage(
        intent="review",
        session_id=session.id,
        project_id="spiel",
        file="main/main.gd",
        code_excerpt=CODE,
        excerpt_start_line=1,
        scene=SCENE,
        input_actions=["springen"],
        project_files=FILES,
        message="Prüfe main/main.gd",
    )
    response = engine.Tutor(session).handle(message)
    assert isinstance(response, LearningResponse) and response.marked_lines == [2, 6, 7]
    system, messages = scripted["provider"].calls[0]
    prompt = messages[0]["content"]
    assert harness.REVIEW_SCENE_NOTE in system and "<befunde>" in system
    assert "- Zeile 2: Datei res://entities/enemies/slime.tscn" in prompt
    assert "- Szene: Timer SpawnTimer startet" in prompt
    assert "autostart, one_shot" in prompt  # missing switches have Godot's default
    assert "Braucht deine Rückmeldung ein weiteres Thema" in prompt
    assert "weitere Stellen markiert" in system and "nur für dieses Skript" in system


def test_python_review_has_no_scene_rules(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    scripted["provider"] = ScriptedProvider(json_answers=[{"feedback": "Gut!", "marked_lines": []}])
    message = StudentMessage(
        intent="review",
        language="python",
        session_id=session.id,
        project_id="rechner",
        file="main.py",
        code_excerpt='load("res://x.tscn")\n',
        excerpt_start_line=1,
        message="Prüfe main.py",
    )
    response = engine.Tutor(session).handle(message)
    assert isinstance(response, LearningResponse) and response.marked_lines == []
    system, messages = scripted["provider"].calls[0]
    assert harness.REVIEW_SCENE_NOTE not in system and "<befunde>" not in messages[0]["content"]
