"""Missions adapt the exercise to the child's stage in the mission's topic."""

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


def test_child_moves_through_the_three_stages(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    for stage, kind in ((1, MultipleChoiceExercise), (2, FillBlanksExercise)):
        for _ in range(harness.STAGE_UP_AFTER):
            assert _level(session) == stage if session.child.skills.exists() else stage == 1
            assert isinstance(_solve(session, scripted, stage), kind)
        assert _level(session) == stage + 1
    assert isinstance(_solve(session, scripted, 3), TextBlanksExercise)
    assert _level(session) == 3


def test_only_first_try_answers_move_the_child_up(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    session.child.set_skill("loops", "Schleifen", 1)
    for _ in range(harness.STAGE_UP_AFTER):
        scripted["provider"] = ScriptedProvider(json_answers=[_answer(1)])
        tutor = engine.Tutor(session)
        exercise = tutor.handle(_start(session)).exercise
        wrong = Submission(exercise_id=exercise.id, answers={"choice": "b"})
        assert tutor.review_submission(wrong).correct is False
        right = Submission(exercise_id=exercise.id, answers={"choice": "a"})
        assert tutor.review_submission(right).correct is True
        assert ExerciseRecord.objects.get(pk=exercise.id).wrong_attempts == 1
    assert _level(session) == 1
    for _ in range(harness.STAGE_UP_AFTER - 1):
        _solve(session, scripted, 1)
    assert _level(session) == 1
    _solve(session, scripted, 1)
    assert _level(session) == 2


def test_wrong_answer_after_solving_changes_nothing(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    exercise = _solve(session, scripted, 1)
    wrong = Submission(exercise_id=exercise.id, answers={"choice": "b"})
    engine.Tutor(session).review_submission(wrong)
    assert ExerciseRecord.objects.get(pk=exercise.id).wrong_attempts == 0


def test_wrong_kind_for_the_stage_is_rejected_once(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    scripted["provider"] = ScriptedProvider(json_answers=[_answer(2), _answer(1)])
    response = engine.Tutor(session).handle(_start(session))
    assert isinstance(response, LearningResponse)
    assert isinstance(response.exercise, MultipleChoiceExercise)
    assert len(scripted["provider"].calls) == 2


def test_typed_answer_never_reaches_the_child_and_accepts_spellings(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    session.child.set_skill("loops", "Schleifen", 3)
    scripted["provider"] = ScriptedProvider(json_answers=[_answer(3)])
    tutor = engine.Tutor(session)
    response = tutor.handle(_start(session))
    assert isinstance(response.exercise, TextBlanksExercise)
    assert "range" not in response.exercise.model_dump_json()
    for typed, right in (("print(5)", False), ("", False), ("range(0,5)", True)):
        review = tutor.review_submission(
            Submission(exercise_id=response.exercise.id, answers={"b1": typed})
        )
        assert review.correct is right


@pytest.mark.parametrize(
    ("typed", "same"),
    [
        ("x+1", True),
        ("x  +  1", True),
        ("'Apfel'", True),
        ("x and y", True),
    ],
)
def test_normalizing_keeps_meaning(typed: str, same: bool) -> None:
    target = {"x+1": "x + 1", "x  +  1": "x+1", "'Apfel'": '"Apfel"', "x and y": "x  and  y"}
    assert (harness.normalize_typed(typed) == harness.normalize_typed(target[typed])) is same


def test_normalizing_does_not_join_words_or_change_text() -> None:
    assert harness.normalize_typed("x and y") != harness.normalize_typed("xandy")
    assert harness.normalize_typed('"a b"') != harness.normalize_typed('"ab"')


def test_other_exercises_do_not_unlock_higher_stages(session: TutorSession) -> None:
    tutor = engine.Tutor(session)
    for _ in range(3):
        tutor._raise_skill("loops")
    assert _level(session) == 1
    for _ in range(3):
        tutor._raise_skill("movement")
    assert _level(session, "movement") == 3


def test_old_mission_without_topic_starts_gently(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    scripted["provider"] = ScriptedProvider(json_answers=[_answer(1, "conditions")])
    response = engine.Tutor(session).handle(_start(session, "movement"))
    assert isinstance(response.exercise, MultipleChoiceExercise)
    assert response.exercise.skill == "Bedingungen"


def test_stage_prompts_ask_for_the_right_format() -> None:
    settings = AiSettings.load()
    assert settings is not None
    assert "multiple_choice" in harness.stage_instructions("loops", 1)
    assert "Dropdown" in harness.stage_instructions("loops", 2)
    assert "selbst ein" in harness.stage_instructions("loops", 3)
    assert harness.mission_exercise_schema(3, "loops")["properties"]["kind"]["enum"] == [
        "text_blanks"
    ]
