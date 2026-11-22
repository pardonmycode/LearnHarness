"""Checks structured AI output; answers stay on the server."""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from learnharness_protocol import Blank, Choice, FillBlanksExercise, MultipleChoiceExercise
from learnharness_protocol.exercises import Exercise

from .rules import SKILLS
from .stream_guard import filter_text, looks_like_code


class HarnessRejected(Exception):
    """The AI output breaks a rule; the reason goes to the log."""


MAX_TODO_SUGGESTIONS = 5


MAX_TODO_LENGTH = 120


def clean_todo_suggestions(items: Any, existing: list[str]) -> list[str]:
    """Keep short, new, code-free to-dos; anything else is dropped."""
    seen = {todo.casefold() for todo in existing}
    result: list[str] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, str) or "`" in item or "\n" in item.strip():
            continue
        text = " ".join(item.split())
        if not text or len(text) > MAX_TODO_LENGTH or looks_like_code(text):
            continue
        if text.casefold() not in seen:
            seen.add(text.casefold())
            result.append(text)
    return result[:MAX_TODO_SUGGESTIONS]


@dataclass
class BuiltExercise:
    exercise: Exercise
    answers: dict[str, str]
    message: str
    skill_id: str
    explanation: str
    new_file_content: str
    notes: list[str]


def build_exercise(data: dict[str, Any], *, max_lines: int, prefix: str) -> BuiltExercise:
    """Turn structured AI output into a protocol exercise; answers stay on the server."""
    exercise_id = f"{prefix}_{uuid4().hex[:12]}"
    skill_id = data.get("skill") if data.get("skill") in SKILLS else "variables"
    message, notes = filter_text(str(data.get("message", "")).strip(), max_lines)
    prompt = str(data.get("prompt", "")).strip()
    code = str(data.get("code", "")).rstrip()
    if not prompt:
        raise HarnessRejected("Übung ohne Aufgabentext")
    if data.get("kind") == "fill_blanks":
        blanks_data = data.get("blanks") or []
        blanks: list[Blank] = []
        answers: dict[str, str] = {}
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
        exercise: Exercise = FillBlanksExercise(
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


def check_answers(expected: dict[str, str], given: dict[str, Any]) -> dict[str, bool]:
    return {key: str(given.get(key, "")).strip() == value for key, value in expected.items()}
