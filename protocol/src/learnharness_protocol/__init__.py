"""Validated messages shared by the LearnHarness client and server."""

from .exercises import (
    Blank,
    Choice,
    Exercise,
    FillBlanksExercise,
    FindBugExercise,
    GeneratedFile,
    MultipleChoiceExercise,
    OrderingExercise,
    OrderItem,
    ReviewItem,
    ReviewResult,
    Submission,
    TextBlank,
    TextBlanksExercise,
)
from .health import HealthStatus
from .messages import (
    CodeSubmission,
    ErrorMessage,
    HintRequest,
    LearningResponse,
    SessionCreate,
    SessionInfo,
    StreamChunk,
    StudentMessage,
    Task,
)
from .progress import ProgressUpdate, Skill, SkillLevel

PROTOCOL_VERSION = "1.1"

__all__ = [
    "PROTOCOL_VERSION",
    "Blank",
    "Choice",
    "CodeSubmission",
    "ErrorMessage",
    "Exercise",
    "FillBlanksExercise",
    "FindBugExercise",
    "GeneratedFile",
    "HealthStatus",
    "HintRequest",
    "LearningResponse",
    "MultipleChoiceExercise",
    "OrderItem",
    "OrderingExercise",
    "ProgressUpdate",
    "ReviewItem",
    "ReviewResult",
    "SessionCreate",
    "SessionInfo",
    "Skill",
    "SkillLevel",
    "StreamChunk",
    "StudentMessage",
    "Submission",
    "Task",
    "TextBlank",
    "TextBlanksExercise",
]
