"""Shared helpers for the tests of mission topics and stages."""

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
from tutor_helpers import ScriptedProvider

from tutor import engine, harness
from tutor.models import AiSettings, ExerciseRecord, TutorSession


def _answer(stage: int, skill: str = "loops") -> dict[str, Any]:
    base: dict[str, Any] = {
        "message": "Los",
        "skill": skill,
        "prompt": "Was fehlt?",
        "code": "",
        "choices": [],
        "blanks": [],
        "explanation_after_correct": "Gut",
        "new_file_content": "",
    }
    if stage == 1:
        base |= {
            "kind": "multiple_choice",
            "choices": [{"text": "a", "correct": True}, {"text": "b", "correct": False}],
        }
    elif stage == 2:
        base |= {
            "kind": "fill_blanks",
            "code": "for i in {{1}}(5):",
            "blanks": [{"options": ["range", "print"], "answer": "range"}],
        }
    else:
        base |= {
            "kind": "text_blanks",
            "code": "for i in {{1}}:",
            "blanks": [{"answer": "range(5)", "alternatives": ["range(0, 5)"]}],
        }
    return base


def _start(session: TutorSession, topic: str | None = "loops") -> StudentMessage:
    mission = Mission(
        id="wunsch-1",
        title="Fünf Münzen",
        goal="Der Fuchs sammelt fünf Münzen.",
        skill=topic,
        steps=[
            MissionStep(id="s1", title="Verstehen", kind="learn"),
            MissionStep(id="s2", title="Ausprobieren", kind="try"),
        ],
    )
    session.wish_missions = {mission.id: mission.model_dump(mode="json")}
    session.save(update_fields=["wish_missions"])
    return StudentMessage(
        intent="mission_step",
        language="python",
        session_id=session.id,
        project_id="spiel",
        mission_id=mission.id,
        mission_step_id="s1",
        message="s1",
    )


def _solve(session: TutorSession, scripted: dict[str, ScriptedProvider], stage: int) -> Any:
    scripted["provider"] = ScriptedProvider(json_answers=[_answer(stage)])
    tutor = engine.Tutor(session)
    response = tutor.handle(_start(session))
    assert isinstance(response, LearningResponse) and response.exercise is not None
    exercise = response.exercise
    answers: dict[str, Any] = {"choice": "a"} if stage == 1 else {"b1": "range"}
    if stage == 3:
        answers = {"b1": "range( 5 )"}
    assert tutor.review_submission(Submission(exercise_id=exercise.id, answers=answers)).correct
    return exercise


def _level(session: TutorSession, topic: str = "loops") -> int:
    return session.child.skills.get(skill_id=topic).level


def _plan(skill: str) -> dict[str, Any]:
    return {
        "title": "Münzen",
        "goal": "Zählen",
        "message": "Los",
        "skill": skill,
        "steps": [{"title": "Verstehen", "kind": "learn"}, {"title": "Probieren", "kind": "try"}],
    }
