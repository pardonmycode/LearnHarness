"""Learning rounds and missions."""

from __future__ import annotations

import json

import pytest
from django.test import Client
from learnharness_protocol import LearningResponse, ReviewResult, StudentMessage
from tutor_helpers import PLAYER, ScriptedProvider, _exercise_json, _headers

from children.models import LearningMission, LearningMissionStep
from tutor import engine
from tutor.models import AiCall, ExerciseRecord, TutorSession

pytestmark = pytest.mark.django_db


def test_learn_round_releases_code_only_after_correct_answer(
    client: Client, token: str, session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    scripted["provider"] = ScriptedProvider(json_answers=[_exercise_json()])
    message = StudentMessage(
        intent="learn",
        session_id=session.id,
        project_id="spiel",
        learning_level=3,
        file="player.gd",
        code_excerpt=PLAYER,
        excerpt_start_line=1,
        message="Meine Figur soll springen",
    )
    response = engine.Tutor(session).handle(message)
    assert isinstance(response, LearningResponse) and response.exercise is not None
    exercise_id = response.exercise.id
    system, messages = scripted["provider"].calls[0]
    assert (
        "Lernstufe 3 von 10" in system
        and "<kind>\nMeine Figur soll springen" in (messages[0]["content"])
    )

    def submit(answer: str) -> ReviewResult:
        result = client.post(
            f"/api/v1/exercises/{exercise_id}/submissions",
            {"exercise_id": exercise_id, "session_id": session.id, "answers": {"b1": answer}},
            content_type="application/json",
            **_headers(token),
        )
        return ReviewResult.model_validate(result.json())

    wrong = submit("func")
    assert wrong.correct is False and wrong.generated_files == []
    right = submit("var")
    assert right.correct is True
    assert right.generated_files[0].path == "player.gd"
    assert "jump_force" in right.generated_files[0].content
    assert session.child is not None
    assert session.child.skills.get(skill_id="variables").level == 1

    call = AiCall.objects.get()
    assert call.intent == "learn" and call.ok and call.child == session.child
    assert "Meine Figur soll springen" in json.dumps(call.messages, ensure_ascii=False)


def test_too_much_generated_code_is_retried_then_refused(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    whole_game = PLAYER + "".join(f"var v{i} = {i}\n" for i in range(30))
    scripted["provider"] = ScriptedProvider(
        json_answers=[_exercise_json(new_file_content=whole_game), _exercise_json()]
    )
    message = StudentMessage(
        intent="learn",
        session_id=session.id,
        project_id="spiel",
        learning_level=3,
        file="player.gd",
        code_excerpt=PLAYER,
        message="Bau mir das ganze Spiel",
    )
    response = engine.Tutor(session).handle(message)
    assert isinstance(response, LearningResponse)
    retry_messages = scripted["provider"].calls[1][1]
    assert "geänderte Zeilen" in retry_messages[-1]["content"]
    calls = list(AiCall.objects.order_by("created_at", "pk"))
    assert [c.ok for c in calls] == [False, True]
    assert calls[0].intervened and "verworfen" in calls[0].harness_notes[0]


def test_mission_step_uses_the_teacher_note(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    mission = LearningMission.objects.create(mission_id="sprung", title="Sprung", goal="Springen!")
    LearningMissionStep.objects.create(
        mission=mission,
        step_id="lernen",
        title="Variable",
        kind="learn",
        note="Betone, dass Namen klein geschrieben werden.",
    )
    first_stage = _exercise_json(
        kind="multiple_choice",
        code="",
        blanks=[],
        choices=[{"text": "var", "correct": True}, {"text": "if", "correct": False}],
    )
    scripted["provider"] = ScriptedProvider(json_answers=[first_stage])
    message = StudentMessage(
        intent="mission_step",
        session_id=session.id,
        project_id="spiel",
        file="player.gd",
        code_excerpt=PLAYER,
        mission_id="sprung",
        mission_step_id="lernen",
        message="lernen",
    )
    response = engine.Tutor(session).handle(message)
    assert isinstance(response, LearningResponse) and response.exercise is not None
    assert "klein geschrieben" in scripted["provider"].calls[0][1][0]["content"]
    record = ExerciseRecord.objects.get(pk=response.exercise.id)
    assert record.generated_content == ""  # only "exercise" steps release code


def test_wish_mission_is_planned_and_its_steps_work(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    scripted["provider"] = ScriptedProvider(
        json_answers=[
            {
                "title": "Münzen sammeln",
                "goal": "Sammle Münzen ein.",
                "message": "Los geht's!",
                "skill": "variables",
                "steps": [
                    {"title": "Was ist ein Signal?", "kind": "understand"},
                    {"title": "Zähler anlegen", "kind": "exercise"},
                ],
            },
            _exercise_json(
                kind="multiple_choice",
                blanks=[],
                choices=[{"text": "ja", "correct": True}, {"text": "nein", "correct": False}],
            ),
        ]
    )
    tutor = engine.Tutor(session)
    base = {"session_id": session.id, "project_id": "spiel", "file": "player.gd"}
    planned = tutor.handle(StudentMessage(intent="mission", message="Münzen!", **base))
    assert isinstance(planned, LearningResponse) and planned.mission is not None
    assert [s.kind for s in planned.mission.steps] == ["understand", "exercise", "try"]
    step = tutor.handle(
        StudentMessage(
            intent="mission_step",
            message="s1",
            mission_id=planned.mission.id,
            mission_step_id="s1",
            **base,
        )
    )
    assert isinstance(step, LearningResponse) and step.exercise is not None


def test_learn_round_rejects_code_that_drops_the_childs_lines(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    scripted["provider"] = ScriptedProvider(
        json_answers=[_exercise_json(new_file_content="# nur neu\nprint(1)\n"), _exercise_json()]
    )
    message = StudentMessage(
        intent="learn",
        session_id=session.id,
        project_id="spiel",
        file="player.gd",
        code_excerpt=PLAYER,
        message="Lass die Figur springen",
    )
    response = engine.Tutor(session).handle(message)
    assert isinstance(response, LearningResponse) and response.exercise is not None
    assert "vorhandene Zeilen" in scripted["provider"].calls[1][1][-1]["content"]
    record = ExerciseRecord.objects.get(pk=response.exercise.id)
    assert record.generated_content.startswith(PLAYER)
