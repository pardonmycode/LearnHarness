"""Checks structured AI output; answers stay on the server."""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from learnharness_protocol import (
    Blank,
    Choice,
    FillBlanksExercise,
    MultipleChoiceExercise,
    TextBlank,
    TextBlanksExercise,
)
from learnharness_protocol.exercises import Exercise

from .code_fence import unwrap_code_fence
from .errors import HarnessRejected
from .exercise_kinds import build_find_bug, build_ordering
from .learn_levels import LEVEL_KINDS
from .rules import SKILLS
from .stream_guard import filter_text, looks_like_code
from .topics import MISSION_TOPICS, STAGE_KINDS, normalize_typed

MAX_DESCRIPTION_LENGTH = 2000
MAX_TYPED_BLANKS = 2
MAX_TYPED_ANSWER = 40
PLAN_MIN_ANSWERS = 3  # the AI may call the idea clear from here on
PLAN_ENOUGH_ANSWERS = 5  # from here on the child is always told it can start


def clean_description(text: Any, current: str) -> str | None:
    """A proposal for the description, or None if it is empty, unchanged or contains code."""
    if not isinstance(text, str):
        return None
    clean = text.strip()
    if not clean or len(clean) > MAX_DESCRIPTION_LENGTH or "`" in clean:
        return None
    if any(looks_like_code(line.strip()) for line in clean.splitlines()):
        return None
    return None if clean.casefold() == current.strip().casefold() else clean


@dataclass
class BuiltExercise:
    exercise: Exercise
    answers: dict[str, Any]
    message: str
    skill_id: str
    explanation: str
    new_file_content: str
    notes: list[str]


def _text_blanks(
    data: dict[str, Any], exercise_id: str, skill_id: str, prompt: str, code: str
) -> tuple[Exercise, dict[str, str | list[str]]]:
    """Blanks the child types; every accepted spelling stays on the server."""
    blanks_data = data.get("blanks") or []
    if not 1 <= len(blanks_data) <= MAX_TYPED_BLANKS:
        raise HarnessRejected("Tippaufgabe braucht ein bis zwei Lücken")
    blanks: list[TextBlank] = []
    answers: dict[str, str | list[str]] = {}
    for index, blank in enumerate(blanks_data, start=1):
        answer = str(blank.get("answer", "")).strip()
        if not answer or len(answer) > MAX_TYPED_ANSWER:
            raise HarnessRejected("Tippantwort fehlt oder ist zu lang")
        others = [str(item).strip() for item in blank.get("alternatives") or []]
        blank_id = f"b{index}"
        code = code.replace(f"{{{{{index}}}}}", f"{{{{{blank_id}}}}}")
        blanks.append(TextBlank(id=blank_id))
        answers[blank_id] = [answer, *[item for item in others if item]]
    if any(f"{{{{{blank.id}}}}}" not in code for blank in blanks):
        raise HarnessRejected("Lückencode passt nicht zu den Lücken")
    exercise = TextBlanksExercise(
        id=exercise_id,
        skill=SKILLS[skill_id],
        difficulty=3,
        prompt=prompt,
        code=code,
        blanks=blanks,
    )
    return exercise, answers


def build_exercise(
    data: dict[str, Any],
    *,
    max_lines: int,
    prefix: str,
    stage: int | None = None,
    topic: str | None = None,
    level: int | None = None,
) -> BuiltExercise:
    """Turn structured AI output into a protocol exercise; answers stay on the server.

    With a stage or a LearnAgent level, only the kind of exercise it uses is accepted."""
    exercise: Exercise
    exercise_id = f"{prefix}_{uuid4().hex[:12]}"
    allowed = MISSION_TOPICS if stage else SKILLS
    skill_id = topic or (data.get("skill") if data.get("skill") in allowed else "variables")
    required = STAGE_KINDS[stage] if stage else LEVEL_KINDS.get(level or 0)
    if required and data.get("kind") != required:
        raise HarnessRejected(f"Hier ist nur die Aufgabenart {required} erlaubt")
    message, notes = filter_text(str(data.get("message", "")).strip(), max_lines)
    prompt = str(data.get("prompt", "")).strip()
    code = unwrap_code_fence(str(data.get("code", ""))).rstrip()
    if not prompt:
        raise HarnessRejected("Übung ohne Aufgabentext")
    answers: dict[str, Any]
    if required == "ordering":
        exercise, answers = build_ordering(data, exercise_id, SKILLS[skill_id], prompt)
    elif required == "find_bug":
        exercise, answers = build_find_bug(data, exercise_id, SKILLS[skill_id], prompt)
    elif required == "text_blanks":
        exercise, answers = _text_blanks(data, exercise_id, skill_id, prompt, code)
    elif data.get("kind") == "fill_blanks":
        blanks_data = data.get("blanks") or []
        blanks: list[Blank] = []
        answers = {}
        for index, blank in enumerate(blanks_data, start=1):
            options = [str(option) for option in blank.get("options", []) if str(option).strip()]
            answer = str(blank.get("answer", ""))
            if answer not in options:
                options.append(answer)
            if len(set(options)) < 2:
                raise HarnessRejected("Lücke mit weniger als zwei Möglichkeiten")
            blank_id = f"b{index}"
            code = code.replace(f"{{{{{index}}}}}", f"{{{{{blank_id}}}}}")
            blanks.append(Blank(id=blank_id, options=sorted(set(options), key=options.index)))
            answers[blank_id] = answer
        if not blanks or any(f"{{{{{blank.id}}}}}" not in code for blank in blanks):
            raise HarnessRejected("Lückencode passt nicht zu den Lücken")
        exercise = FillBlanksExercise(
            id=exercise_id,
            skill=SKILLS[skill_id],
            difficulty=2,
            prompt=prompt,
            code=code,
            blanks=blanks,
        )
    else:
        choices_data = data.get("choices") or []
        correct = [index for index, choice in enumerate(choices_data) if choice.get("correct")]
        if len(choices_data) < 2 or len(correct) != 1:
            raise HarnessRejected("Auswahlaufgabe braucht genau eine richtige Antwort")
        choices = [
            Choice(id=chr(ord("a") + index), text=str(choice.get("text", "")))
            for index, choice in enumerate(choices_data[:6])
        ]
        exercise = MultipleChoiceExercise(
            id=exercise_id,
            skill=SKILLS[skill_id],
            difficulty=1,
            prompt=prompt,
            code=code or None,
            choices=choices,
        )
        answers = {"choice": chr(ord("a") + correct[0])}
    explanation, more = filter_text(str(data.get("explanation_after_correct", "")), max_lines)
    return BuiltExercise(
        exercise=exercise,
        answers=answers,
        message=message,
        skill_id=skill_id,
        explanation=explanation.strip(),
        new_file_content=str(data.get("new_file_content", "")),
        notes=notes + more,
    )


def changed_lines(before: str, after: str) -> int:
    diff = list(difflib.ndiff(before.splitlines(), after.splitlines()))
    added = sum(1 for line in diff if line.startswith("+ "))
    removed = sum(1 for line in diff if line.startswith("- "))
    return max(added, removed)


def check_generated_code(before: str, after: str, max_changed: int) -> str | None:
    """Return a reason when the released code would hand over too much, else None."""
    if not after.strip():
        return "kein Code geliefert"
    count = changed_lines(before, after)
    if count == 0:
        return "keine Änderung"
    if count > max_changed:
        return f"{count} geänderte Zeilen (erlaubt: {max_changed})"
    return None


def _answer_matches(expected: Any, given: Any) -> bool:
    if isinstance(expected, dict):  # sorted items or chosen lines: the exact list counts
        wanted = [str(item) for item in expected["exact"]]
        return isinstance(given, list) and [str(item) for item in given] == wanted
    text = str(given if given is not None else "").strip()
    if isinstance(expected, list):  # typed by the child: several spellings are right
        return bool(text) and normalize_typed(text) in {normalize_typed(v) for v in expected}
    return text == expected


def check_answers(expected: dict[str, Any], given: dict[str, Any]) -> dict[str, bool]:
    return {key: _answer_matches(value, given.get(key, "")) for key, value in expected.items()}
