"""Missions pick a topic and follow the learning order."""

from __future__ import annotations

from typing import Any

import pytest
from learnharness_protocol import (
    FillBlanksExercise,
    LearningResponse,
    Mission,
    MissionStep,
    MultipleChoiceExercise,
    StudentMessage,
    Submission,
    TextBlanksExercise,
)
from mission_helpers import _answer, _level, _plan, _solve, _start
from tutor_helpers import ScriptedProvider

from tutor import engine, harness
from tutor.models import AiSettings, ExerciseRecord, TutorSession

pytestmark = pytest.mark.django_db


def test_mission_prompt_offers_the_topics_and_stages(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    session.child.set_skill("loops", "Schleifen", 2)
    scripted["provider"] = ScriptedProvider(
        json_answers=[
            {
                "title": "Münzen",
                "goal": "Zählen",
                "message": "Los",
                "skill": "arrays",
                "steps": [
                    {"title": "Verstehen", "kind": "learn"},
                    {"title": "Probieren", "kind": "try"},
                ],
            }
        ]
    )
    message = StudentMessage(
        intent="mission", session_id=session.id, project_id="spiel", message="Inventar"
    )
    response = engine.Tutor(session).handle(message)
    assert isinstance(response, LearningResponse) and response.mission.skill == "arrays"
    system, messages = scripted["provider"].calls[0]
    for topic in harness.MISSION_TOPICS:
        assert f"- {topic}:" in system
    assert "- loops: Stufe 2" in messages[0]["content"]
    assert "- arrays: noch nicht begonnen" in messages[0]["content"]
    assert "<kind>\nInventar" in messages[0]["content"]  # a real wish stays the child's message
    assert harness.MISSION_SCHEMA["properties"]["skill"]["enum"] == list(harness.MISSION_TOPICS)


def test_learning_order_and_reachable_topics() -> None:
    assert list(harness.MISSION_TOPICS) == [
        "variables",
        "operators",
        "conditions",
        "loops",
        "functions",
        "arrays",
        "classes",
    ]
    assert harness.reachable_topics({}) == ["variables"]
    assert harness.reachable_topics({"variables": 1}) == ["variables"]
    assert harness.reachable_topics({"variables": 2}) == ["variables", "operators"]
    assert harness.reachable_topics({"variables": 3, "operators": 1, "conditions": 3}) == [
        "variables",
        "operators",
    ]
    assert harness.reachable_topics(dict.fromkeys(harness.MISSION_TOPICS, 1)) == ["variables"]
    assert harness.reachable_topics(dict.fromkeys(harness.MISSION_TOPICS, 2)) == list(
        harness.MISSION_TOPICS
    )


def test_project_button_follows_the_order_without_a_fake_message(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    session.child.set_skill("variables", "Variablen", 2)
    scripted["provider"] = ScriptedProvider(json_answers=[_plan("classes"), _plan("operators")])
    message = StudentMessage(
        intent="mission",
        session_id=session.id,
        project_id="spiel",
        project_description="Ein Fuchs sammelt Münzen",
        mission_from_project=True,
        message="Was ist der nächste kleine Baustein für mein Projekt?",
    )
    response = engine.Tutor(session).handle(message)
    assert isinstance(response, LearningResponse) and response.mission.skill == "operators"
    calls = scripted["provider"].calls
    assert len(calls) == 2
    first = calls[0][1][0]["content"]
    assert "<kind>" not in first and "Nachricht des Kindes" not in first
    assert "keinen eigenen Wunsch" in first and "Themen: variables, operators" in first


def test_explicit_wish_may_use_a_later_topic(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    scripted["provider"] = ScriptedProvider(json_answers=[_plan("classes")])
    message = StudentMessage(
        intent="mission", session_id=session.id, project_id="spiel", message="Ich will Klassen"
    )
    response = engine.Tutor(session).handle(message)
    assert isinstance(response, LearningResponse) and response.mission.skill == "classes"


def test_project_button_stays_on_a_topic_below_stage_two(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    session.child.set_skill("variables", "Variablen", 1)
    scripted["provider"] = ScriptedProvider(json_answers=[_plan("operators"), _plan("variables")])
    message = StudentMessage(
        intent="mission",
        session_id=session.id,
        project_id="spiel",
        project_description="Ein Fuchs sammelt Münzen",
        mission_from_project=True,
        message="Was ist der nächste kleine Baustein für mein Projekt?",
    )
    response = engine.Tutor(session).handle(message)
    assert isinstance(response, LearningResponse) and response.mission.skill == "variables"
    assert (
        "mit einem dieser Themen: variables\n"
        in scripted["provider"].calls[0][1][0]["content"] + "\n"
    )


def test_mission_prompt_handles_wish_and_button() -> None:
    system = harness.system_prompt("mission", AiSettings.load(), language="python")
    assert "Plane aus dem Wunsch" not in system
    assert "Fehlt <kind>, entsteht sie aus <projekt>" in system
    assert "mindestens Stufe 2" in system
