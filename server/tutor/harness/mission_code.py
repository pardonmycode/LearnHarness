"""Keeps a mission exercise and the code released after it in line."""

from __future__ import annotations

import ast
import difflib
import re
import warnings
from collections import Counter
from typing import Any

from .topics import MAX_EXERCISE_CODE_LINES, normalize_typed

_BLANK = re.compile(r"\{\{(\w+)\}\}")
_ASSIGNED_BLANK = re.compile(r"^\s*(?:var\s+)?\w+\s*(?::\s*\w*\s*)?=\s*\{\{(\w+)\}\}\s*(?:#.*)?$")
_NUMBER = re.compile(r"^-?\d+(?:\.\d+)?$")
MAX_LOST_LINES = 2
SAME_LINE_RATIO = 0.6  # a line this similar was changed, not removed


def _first(value: Any) -> str:
    return str(value[0] if isinstance(value, list) else value)


def _fill(line: str, values: dict[str, str]) -> str:
    return _BLANK.sub(lambda match: values.get(match.group(1), match.group(0)), line).strip()


def _code_part(line: str) -> str:
    """The line without a trailing comment."""
    return line.split("#", 1)[0].strip()


def _blank_lines(code: str) -> list[str]:
    return [line for line in code.splitlines() if _BLANK.search(line)]


def check_blanks_in_file(code: str, answers: dict[str, Any], new_file: str) -> str | None:
    """A reason when a solved line of the exercise is missing from the released code."""
    solution = {key: _first(value) for key, value in answers.items()}
    in_file = {normalize_typed(_code_part(line)) for line in new_file.splitlines()}
    for line in _blank_lines(code):
        filled = _fill(line, solution)
        if normalize_typed(filled) not in in_file:
            return f"Die gelöste Zeile „{filled}“ fehlt in new_file_content"
    return None


def apply_typed_answers(
    new_file: str, code: str, expected: dict[str, Any], given: dict[str, Any]
) -> str:
    """Put the child's own correct spelling into the released code.

    Only a line that is found exactly once is changed; otherwise the checked code stays."""
    if not any(isinstance(value, list) for value in expected.values()):
        return new_file
    typed = {key: str(given.get(key, "")).strip() for key in expected}
    if any(not text or "\n" in text or "\r" in text for text in typed.values()):
        return new_file
    solution = {key: _first(value) for key, value in expected.items()}
    lines = new_file.splitlines(keepends=True)
    for line in _blank_lines(code):
        planned, own = _fill(line, solution), _fill(line, typed)
        if planned == own:
            continue
        found = [index for index, item in enumerate(lines) if _code_part(item) == planned]
        if len(found) == 1:
            lines[found[0]] = lines[found[0]].replace(planned, own, 1)
    return "".join(lines)


def check_keeps_code(before: str, after: str) -> str | None:
    """A reason when the new file drops the child's code instead of building on it."""
    old = [line.strip() for line in before.splitlines() if line.strip()]
    new = [line.strip() for line in after.splitlines() if line.strip()]
    gone = list((Counter(old) - Counter(new)).elements())
    added = list((Counter(new) - Counter(old)).elements())
    lost = 0
    for line in gone:
        match = next(
            (
                item
                for item in added
                if difflib.SequenceMatcher(None, line, item).ratio() >= SAME_LINE_RATIO
            ),
            None,
        )
        if match is None:
            lost += 1
        else:
            added.remove(match)
    allowed = min(MAX_LOST_LINES, len(old) // 2)
    if lost > allowed:
        return f"{lost} vorhandene Zeilen des Kindes fehlen (erlaubt: {allowed})"
    return None


def _value_is_named(answer: str, prompt: str) -> bool:
    """A free value like 5 or "Fuchs" has to come from the task, or anything would be right."""
    text = answer.strip()
    if _NUMBER.match(text):
        return any(char.isdigit() for char in prompt)
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1].casefold() in prompt.casefold()
    return True


def _is_code_answer(answer: str) -> bool:
    """Expressions like range(5); plain names and free values may be part of a task."""
    text = answer.strip()
    if _NUMBER.match(text) or (len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'"):
        return False
    return bool(re.search(r"[^\w\s]", text))


def _squeezed(text: str) -> str:
    return re.sub(r"\s+", "", text)


def check_blanks_are_clear(exercise: Any, answers: dict[str, Any], message: str = "") -> str | None:
    """A reason when a right answer could be marked wrong or the task gives it away."""
    code = str(getattr(exercise, "code", "") or "")
    if len(code.splitlines()) > MAX_EXERCISE_CODE_LINES:
        return f"Der Code der Übung hat mehr als {MAX_EXERCISE_CODE_LINES} Zeilen"
    for blank in getattr(exercise, "blanks", []):
        options = [normalize_typed(option) for option in getattr(blank, "options", [])]
        if len(options) != len(set(options)):
            return "Zwei Optionen sind dieselbe Lösung in anderer Schreibweise"
    for line in code.splitlines():
        match = _ASSIGNED_BLANK.match(line)
        blank = match.group(1) if match else ""
        if blank in answers and not _value_is_named(_first(answers[blank]), exercise.prompt):
            return 'Der frei wählbare Wert der Lücke muss in "prompt" genannt werden'
    if getattr(exercise, "kind", "") in ("fill_blanks", "text_blanks"):
        shown = _squeezed(f"{exercise.prompt} {message}")
        for value in answers.values():
            for answer in value if isinstance(value, list) else [value]:
                if _is_code_answer(str(answer)) and _squeezed(str(answer)) in shown:
                    return "Aufgabentext oder Nachricht verraten die Lösung"
    return None


def check_python_syntax(before: str, after: str) -> str | None:
    """A reason when working Python would be replaced by code that cannot start."""

    def error(text: str) -> str | None:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ast.parse(text)
        except SyntaxError as exc:
            return f"Zeile {exc.lineno}: {exc.msg}"
        except (ValueError, RecursionError, MemoryError):
            return "nicht lesbar"
        return None

    problem = error(after)
    if problem is None or error(before) is not None:
        return None  # the child's script was already broken: do not block the help
    return f"Syntaxfehler im neuen Code, {problem}"
