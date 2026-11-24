"""Session, tutor, task, and error messages."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from .base import ProtocolModel
from .exercises import Exercise
from .missions import Mission

# chat: tutor chat · learn: LearnAgent round · explain: explain selected code
# mission: start a mission from a wish · mission_step: work on one mission step
# project_plan: ask the child questions so its project description gets clearer
# review: feedback on the open script, without exercise and without progress
StudentIntent = Literal[
    "chat", "learn", "explain", "mission", "mission_step", "project_plan", "review"
]
MissionTitle = Annotated[str, Field(min_length=1, max_length=120)]
ProjectQuestion = Annotated[str, Field(min_length=1, max_length=1000)]


class ProjectTurn(ProtocolModel):
    """One question of the helper about the project and the child's answer."""

    question: str = Field(min_length=1, max_length=1000)
    answer: str = Field(min_length=1, max_length=1000)


class StudentMessage(ProtocolModel):
    type: Literal["student_message"] = "student_message"
    intent: StudentIntent = "chat"
    session_id: str
    project_id: str
    experience_level: int = Field(default=0, ge=0, le=3)
    learning_level: int | None = Field(default=None, ge=1, le=10)
    language: Literal["gdscript", "python"] = "gdscript"
    current_task: str | None = None
    file: str | None = None
    code_excerpt: str | None = None
    excerpt_start_line: int | None = Field(default=None, ge=1)
    last_error: str | None = None
    # Skill the child should practise next (e.g. "conditions"). Only a wish: the server
    # still decides the exercise and still releases code only after a correct answer.
    skill_focus: str | None = Field(default=None, max_length=64)
    mission_id: str | None = Field(default=None, max_length=64)
    mission_step_id: str | None = Field(default=None, max_length=64)
    # Started with the project button: the child named no wish of its own.
    mission_from_project: bool = False
    # The hint button in a project: which of the four hint levels is wanted.
    project_hint_level: int | None = Field(default=None, ge=1, le=4)
    project_description: str | None = Field(default=None, max_length=2000)
    project_question: str | None = Field(default=None, max_length=1000)
    project_turns: list[ProjectTurn] = Field(default_factory=list, max_length=12)
    # Questions the child did not want to answer; the helper must not ask them again.
    project_skipped_questions: list[ProjectQuestion] = Field(
        default_factory=list, max_length=8
    )
    # Finished missions, so the next one builds on them instead of repeating them.
    project_done_missions: list[MissionTitle] = Field(
        default_factory=list, max_length=30
    )
    message: str = Field(min_length=1, max_length=4000)


class StreamChunk(ProtocolModel):
    type: Literal["stream_chunk"] = "stream_chunk"
    text: str


class LearningResponse(ProtocolModel):
    type: Literal["learning_response"] = "learning_response"
    mode: Literal[
        "socratic",
        "hint",
        "exercise",
        "explanation",
        "review",
        "mission",
        "project_plan",
    ]
    message: str
    hint_level: int = Field(default=0, ge=0, le=4)
    hints: list[str] = Field(default_factory=list)
    exercise: Exercise | None = None
    mission: Mission | None = None
    # Only a proposal: the description changes when the child accepts it.
    description_suggestion: str | None = Field(default=None, max_length=2000)
    project_ready: bool = False
    # Lines of the reviewed script that need a look (only for mode "review").
    marked_lines: list[int] = Field(default_factory=list, max_length=50)
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
