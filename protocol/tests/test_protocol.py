from __future__ import annotations

import pytest
from learnharness_protocol import (
    Exercise,
    FillBlanksExercise,
    GeneratedFile,
    LearningResponse,
    ReviewResult,
    SessionCreate,
    StudentMessage,
)
from pydantic import TypeAdapter, ValidationError


def test_pdf_student_message_parses() -> None:
    message = StudentMessage.model_validate(
        {
            "type": "student_message",
            "protocol_version": "1.0",
            "session_id": "session_001",
            "project_id": "survival_game",
            "language": "gdscript",
            "current_task": "move_player_right",
            "file": "player.gd",
            "code_excerpt": "position.y += 10",
            "excerpt_start_line": 1,
            "last_error": None,
            "message": "Warum funktioniert mein Code nicht?",
        }
    )
    assert message.language == "gdscript"


def test_exercise_has_no_solution_field() -> None:
    data = {
        "kind": "fill_blanks",
        "protocol_version": "1.0",
        "id": "exercise_001",
        "skill": "coordinates",
        "difficulty": 1,
        "prompt": "Ergänze die Variable.",
        "code": "position.{{blank_1}} += 10",
        "blanks": [
            {
                "protocol_version": "1.0",
                "id": "blank_1",
                "options": ["x", "y", "speed"],
            }
        ],
    }
    exercise = TypeAdapter(Exercise).validate_python(data)
    assert isinstance(exercise, FillBlanksExercise)
    with pytest.raises(ValidationError):
        TypeAdapter(Exercise).validate_python({**data, "solution": "x"})


def test_unknown_response_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        LearningResponse.model_validate(
            {
                "type": "learning_response",
                "mode": "socratic",
                "message": "Welche Achse?",
                "surprise": True,
            }
        )


def test_incompatible_major_version_is_rejected() -> None:
    with pytest.raises(ValidationError):
        StudentMessage(
            protocol_version="2.0",
            session_id="s",
            project_id="p",
            message="Hallo",
        )


def test_session_carries_pseudonymous_profile_and_level() -> None:
    session = SessionCreate(
        project_id="project",
        client_version="0.1.0",
        student_profile_id="abc123",
        student_pseudonym="CodeFuchs",
        experience_level=2,
    )
    assert session.student_profile_id == "abc123"
    assert session.experience_level == 2

    with pytest.raises(ValidationError):
        SessionCreate(
            project_id="project",
            client_version="0.1.0",
            student_profile_id="abc123",
            student_pseudonym="CodeFuchs",
            experience_level=4,
        )


def test_generated_code_requires_correct_answer() -> None:
    generated = GeneratedFile(
        path="player.gd",
        content="extends Node2D\n",
        explanation="Das Skript erbt von Node2D.",
    )
    with pytest.raises(ValidationError):
        ReviewResult(
            correct=False,
            feedback="Noch einmal versuchen.",
            generated_files=[generated],
        )
    accepted = ReviewResult(
        correct=True,
        feedback="Richtig.",
        generated_files=[generated],
    )
    assert accepted.generated_files[0].path == "player.gd"
