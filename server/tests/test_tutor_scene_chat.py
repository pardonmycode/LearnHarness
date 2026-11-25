"""Chat, hints and reviews read the scene too, without being able to change it."""

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
from tutor.models import AiSettings, TutorSession

pytestmark = pytest.mark.django_db

SCENE = SceneContext(
    path="entities/player/player.tscn",
    root_name="Player",
    script_node=".",
    nodes=[
        SceneNode(path=".", type="CharacterBody2D", script="res://entities/player/player.gd"),
        SceneNode(path="Hitbox", type="Area2D"),
        SceneNode(path="Hud", instance="res://ui/hud/hud.tscn"),
    ],
    connections=[
        SceneConnection(signal="body_entered", from_node="Hitbox", to_node=".", method="_on_hit"),
        SceneConnection(signal="ready", from_node=".", to_node="Hud", method="_start"),
    ],
)


def test_signals_name_the_root_instead_of_a_dot() -> None:
    text = harness.scene_tree_text(SCENE)
    assert "- Hitbox.body_entered → Player._on_hit()" in text
    assert "- Player.ready → Hud._start()" in text and ".." not in text


def test_chat_explains_the_scene_block_and_gets_the_files(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    scripted["provider"] = ScriptedProvider(chunks=["Schau mal auf den Namen."])
    message = StudentMessage(
        session_id=session.id,
        project_id="spiel",
        file="entities/player/player.gd",
        code_excerpt="extends CharacterBody2D\n",
        scene=SCENE,
        project_files=["main/main.tscn"],
        message="Warum wird mein Fuchs nicht rot?",
    )
    response = engine.Tutor(session).handle(message)
    assert isinstance(response, LearningResponse)
    system, messages = scripted["provider"].calls[0]
    prompt = messages[-1]["content"]
    assert harness.SCENE_HEADER in prompt and "nicht aufgeführt" in prompt
    assert "„ui_left“" in prompt and "<eingaben>\n(keine eigenen)\n</eingaben>" in prompt
    assert "<dateien>\nres://main/main.tscn" in prompt
    assert harness.CHAT_SCENE_NOTE in system


def test_python_chat_gets_no_scene_note() -> None:
    system = harness.system_prompt("chat", AiSettings.load(), language="python")
    assert harness.CHAT_SCENE_NOTE not in system
    assert "kann ein\nAusschnitt sein" in system
    hint = harness.system_prompt("hint", AiSettings.load(), hint_level=2, language="python")
    assert "kann ein Ausschnitt sein" in hint


def test_explaining_code_uses_the_scene_but_no_lists() -> None:
    message = StudentMessage(
        intent="explain",
        session_id="s",
        project_id="spiel",
        code_excerpt="extends Node\n",
        scene=SCENE,
        project_files=["main/main.tscn"],
        message="Was macht das?",
    )
    prompt = harness.user_prompt(message)
    assert "<szene>" in prompt and "<dateien>" not in prompt and "<eingaben>" not in prompt
    system = harness.system_prompt("explain", AiSettings.load(), language="gdscript")
    assert harness.EXPLAIN_SCENE_NOTE in system and "kann ein Ausschnitt sein" in system
    python = harness.system_prompt("explain", AiSettings.load(), language="python")
    assert harness.EXPLAIN_SCENE_NOTE not in python and "kann ein Ausschnitt sein" in python
