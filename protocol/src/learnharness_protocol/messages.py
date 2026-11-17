"""Session, tutor, task, and error messages."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from .base import ProtocolModel
from .exercises import Exercise


class StudentMessage(ProtocolModel):
    type: Literal["student_message"] = "student_message"
    session_id: str
    project_id: str
    experience_level: int = Field(default=0, ge=0, le=3)
    learning_level: int | None = Field(default=None, ge=1, le=10)
    language: Literal["gdscript"] = "gdscript"
    current_task: str | None = None
    file: str | None = None
    code_excerpt: str | None = None
    excerpt_start_line: int | None = Field(default=None, ge=1)
    last_error: str | None = None
    message: str = Field(min_length=1, max_length=4000)


class StreamChunk(ProtocolModel):
    type: Literal["stream_chunk"] = "stream_chunk"
    text: str


class LearningResponse(ProtocolModel):
    type: Literal["learning_response"] = "learning_response"
    mode: Literal["socratic", "hint", "exercise", "explanation", "review"]
    message: str
    hint_level: int = Field(default=0, ge=0, le=4)
    hints: list[str] = Field(default_factory=list)
    exercise: Exercise | None = None
    code_changes: list[dict[str, object]] = Field(default_factory=list)


class ErrorMessage(ProtocolModel):
    type: Literal["error"] = "error"
    code: str
    message_for_child: str
    retry_after: int | None = Field(default=None, ge=0)


class SessionCreate(ProtocolModel):
    type: Literal["session_create"] = "session_create"
    project_id: str
    client_version: str
    student_profile_id: str = Field(min_length=1, max_length=64)
    student_pseudonym: str = Field(min_length=2, max_length=30)
    experience_level: int = Field(ge=0, le=3)


class SessionInfo(ProtocolModel):
    type: Literal["session_info"] = "session_info"
    session_id: str
    student_pseudonym: str
    current_task_id: str | None = None


class HintRequest(ProtocolModel):
    type: Literal["hint_request"] = "hint_request"
    task_id: str


class Task(ProtocolModel):
    type: Literal["task"] = "task"
    id: str
    title: str
    skill: str
    instructions: str
    files: list[str] = Field(default_factory=list)


class CodeSubmission(ProtocolModel):
    type: Literal["code_submission"] = "code_submission"
    task_id: str
    session_id: str
    file: str
    content: str


IncomingMessage = Annotated[
    StreamChunk | LearningResponse | ErrorMessage | Task,
    Field(discriminator="type"),
]
