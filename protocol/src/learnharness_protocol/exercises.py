"""Exercise payloads never include the correct solution."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .base import ProtocolModel


class Blank(ProtocolModel):
    id: str
    options: list[str] = Field(min_length=1)


class TextBlank(ProtocolModel):
    id: str
    placeholder: str = "Antwort eingeben"


class Choice(ProtocolModel):
    id: str
    text: str


class OrderItem(ProtocolModel):
    id: str
    text: str


class ExerciseBase(ProtocolModel):
    id: str
    skill: str
    difficulty: int = Field(ge=1, le=5)
    prompt: str


class FillBlanksExercise(ExerciseBase):
    kind: Literal["fill_blanks"] = "fill_blanks"
    code: str
    blanks: list[Blank] = Field(min_length=1)


class MultipleChoiceExercise(ExerciseBase):
    kind: Literal["multiple_choice"] = "multiple_choice"
    code: str | None = None
    choices: list[Choice] = Field(min_length=2)
    multiple: bool = False


class OrderingExercise(ExerciseBase):
    kind: Literal["ordering"] = "ordering"
    items: list[OrderItem] = Field(min_length=2)


class FindBugExercise(ExerciseBase):
    kind: Literal["find_bug"] = "find_bug"
    lines: list[str] = Field(min_length=1)
    allow_multiple: bool = False


class TextBlanksExercise(ExerciseBase):
    kind: Literal["text_blanks"] = "text_blanks"
    code: str
    blanks: list[TextBlank] = Field(min_length=1)


Exercise = Annotated[
    FillBlanksExercise
    | MultipleChoiceExercise
    | OrderingExercise
    | FindBugExercise
    | TextBlanksExercise,
    Field(discriminator="kind"),
]


class Submission(ProtocolModel):
    type: Literal["exercise_submission"] = "exercise_submission"
    exercise_id: str
    session_id: str | None = None
    answers: dict[str, str | list[str] | int | list[int]]
    explanation: str | None = None


class ReviewItem(ProtocolModel):
    id: str
    correct: bool
    feedback: str | None = None


class GeneratedFile(ProtocolModel):
    path: str = Field(min_length=3, max_length=500)
    content: str = Field(max_length=524_288)
    explanation: str


class ReviewResult(ProtocolModel):
    type: Literal["review_result"] = "review_result"
    correct: bool | None = None
    per_item: list[ReviewItem] = Field(default_factory=list)
    feedback: str
    follow_up_question: str | None = None
    marked_lines: list[int] = Field(default_factory=list)
    generated_files: list[GeneratedFile] = Field(default_factory=list)

    @model_validator(mode="after")
    def generated_code_requires_correct_answer(self) -> ReviewResult:
        if self.generated_files and self.correct is not True:
            raise ValueError(
                "Generierter Code ist nur nach einer richtigen Antwort erlaubt."
            )
        return self
