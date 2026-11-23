"""Keeps a mission exercise and the code released after it in line."""

from __future__ import annotations

import re
from typing import Any

from .topics import normalize_typed

_BLANK = re.compile(r"\{\{(\w+)\}\}")


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
