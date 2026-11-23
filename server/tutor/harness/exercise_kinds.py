"""Ordering and find-the-bug exercises; their solutions stay on the server."""

from __future__ import annotations

import random
from typing import Any

from learnharness_protocol import FindBugExercise, OrderingExercise, OrderItem

from .errors import HarnessRejected
from .topics import MAX_EXERCISE_CODE_LINES, normalize_typed

MIN_LINES = 3


def _lines(items: Any) -> list[str]:
    lines = [str(item).rstrip() for item in items or [] if str(item).strip()]
    if not MIN_LINES <= len(lines) <= MAX_EXERCISE_CODE_LINES:
        raise HarnessRejected(f"Aufgabe braucht {MIN_LINES} bis {MAX_EXERCISE_CODE_LINES} Zeilen")
    if any("```" in line for line in lines):
        raise HarnessRejected("Zeilen dürfen keine Markdown-Codeblöcke enthalten")
    return lines


def build_ordering(
    data: dict[str, Any], exercise_id: str, skill: str, prompt: str
) -> tuple[OrderingExercise, dict[str, Any]]:
    lines = _lines(data.get("ordered_lines"))
    if len({normalize_typed(line) for line in lines}) != len(lines):
        raise HarnessRejected("Gleiche Zeilen erlauben mehrere richtige Reihenfolgen")
    shown = list(range(len(lines)))
    while shown == sorted(shown):
        random.shuffle(shown)
    # Ids follow the shown order, so they say nothing about the solution.
    ids = {line: chr(ord("a") + position) for position, line in enumerate(shown)}
    exercise = OrderingExercise(
        id=exercise_id,
        skill=skill,
        difficulty=3,
        prompt=prompt,
        items=[OrderItem(id=ids[line], text=lines[line]) for line in shown],
    )
    return exercise, {"order": {"exact": [ids[line] for line in range(len(lines))]}}


def build_find_bug(
    data: dict[str, Any], exercise_id: str, skill: str, prompt: str
) -> tuple[FindBugExercise, dict[str, Any]]:
    lines = _lines(data.get("buggy_lines"))
    bug = data.get("bug_line")
    if not isinstance(bug, int) or isinstance(bug, bool) or not 1 <= bug <= len(lines):
        raise HarnessRejected("bug_line muss eine Zeile der Aufgabe sein")
    exercise = FindBugExercise(
        id=exercise_id, skill=skill, difficulty=4, prompt=prompt, lines=lines
    )
    return exercise, {"lines": {"exact": [bug]}}


def _code_lines(text: str) -> list[str]:
    return [normalize_typed(line.split("#", 1)[0]) for line in text.splitlines()]


def check_kind_in_file(
    exercise: Any, answers: dict[str, Any], before: str, new_file: str
) -> str | None:
    """A reason when the released code does not fit a sorting or bug exercise."""
    in_file = _code_lines(new_file)
    if isinstance(exercise, OrderingExercise):
        texts = {item.id: normalize_typed(item.text) for item in exercise.items}
        position = 0
        for item_id in answers["order"]["exact"]:
            try:
                position = in_file.index(texts[item_id], position) + 1
            except ValueError:
                return "Die sortierten Zeilen stehen nicht in dieser Reihenfolge im Code"
    if isinstance(exercise, FindBugExercise):
        wrong = normalize_typed(exercise.lines[answers["lines"]["exact"][0] - 1])
        if wrong in in_file and wrong not in _code_lines(before):
            return "Die falsche Zeile steht im neuen Code"
    return None
