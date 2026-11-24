"""Feedback on the open script: about the project, without progress or a fake message."""

from __future__ import annotations

from typing import Any

import pytest
from learnharness_protocol import ErrorMessage, LearningResponse, StudentMessage
from tutor_helpers import ScriptedProvider

from tutor import engine
from tutor.models import TutorSession

pytestmark = pytest.mark.django_db
CODE = "muenzen = 0\nprint(punkte)\n"


def _message(session: TutorSession, **fields: Any) -> StudentMessage:
    data: dict[str, Any] = {
        "intent": "review",
        "language": "python",
        "session_id": session.id,
        "project_id": "spiel",
        "current_task": "python_first_program",
        "file": "main.py",
        "code_excerpt": CODE,
        "excerpt_start_line": 1,
        "project_description": "Ein Fuchs sammelt Münzen",
        "message": "Bitte prüfe meinen Code in main.py.",
    }
    return StudentMessage(**(data | fields))


def _review(
    session: TutorSession, scripted: dict[str, ScriptedProvider], *answers: Any, **fields: Any
):
    scripted["provider"] = ScriptedProvider(json_answers=list(answers))
    return engine.Tutor(session).handle(_message(session, **fields))


def test_feedback_and_only_real_lines(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    answer = {"feedback": "Schön! Wo kommt punkte her?", "marked_lines": [2, 2, 0, 9, True]}
    response = _review(session, scripted, answer)
    assert isinstance(response, LearningResponse)
    assert response.mode == "review" and response.marked_lines == [2]
    system, messages = scripted["provider"].calls[0]
    prompt = messages[0]["content"]
    assert "Aktuelle Aufgabe" not in prompt and "<projekt>" in prompt
    assert "<kind>" not in prompt and "Beginne mit etwas, das gut ist" in system


def test_review_never_changes_progress(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    _review(session, scripted, {"feedback": "Toll!", "marked_lines": []})
    assert not session.child.skills.exists()


def test_without_a_project_the_example_task_is_checked(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    _review(session, scripted, {"feedback": "Gut.", "marked_lines": []}, project_description=None)
    assert "Aktuelle Aufgabe" in scripted["provider"].calls[0][1][0]["content"]


def test_empty_feedback_gets_a_second_try(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    response = _review(
        session,
        scripted,
        {"feedback": " ", "marked_lines": []},
        {"feedback": "Gut.", "marked_lines": []},
    )
    assert isinstance(response, LearningResponse) and response.message == "Gut."


def test_no_script_no_review(session: TutorSession) -> None:
    response = engine.Tutor(session).handle(_message(session, code_excerpt=None))
    assert isinstance(response, ErrorMessage) and response.code == "no_code"
