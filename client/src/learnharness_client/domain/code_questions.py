"""Suggest child-friendly questions about a piece of GDScript or Python.

The questions are only a starting point for the code explainer; the child can always
ask something else. No network and no AI is involved here.
"""

from __future__ import annotations

import re

_FUNC = re.compile(r"^\s*(?:func|(?:async\s+)?def)\s+([A-Za-z_]\w*)")
_ASSIGN = re.compile(r"^\s*([A-Za-z_][\w.]*)\s*(=|\+=|-=|\*=|/=)\s*(.+?)\s*$")
_CALL = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_VAR = re.compile(r"^\s*(?:@export\s+)?(?:var|const)\s+([A-Za-z_]\w*)")
_EXTENDS = re.compile(r"^\s*extends\s+(\w+)")
_KEYWORDS = {
    "if",
    "elif",
    "while",
    "for",
    "func",
    "def",
    "return",
    "match",
    "print",
    "range",
    "and",
    "or",
    "not",
    "in",
}

MAX_QUESTIONS = 4


def _strip_comment(line: str) -> str:
    in_string: str | None = None
    for index, character in enumerate(line):
        if character in "\"'":
            in_string = None if in_string == character else in_string or character
        elif character == "#" and in_string is None:
            return line[:index]
    return line


def code_questions(code: str, limit: int = MAX_QUESTIONS) -> list[str]:
    # (priority, question): statements and calls first, declarations last.
    found: list[tuple[int, str]] = []

    def add(priority: int, question: str) -> None:
        if all(question != existing for _, existing in found):
            found.append((priority, question))

    for raw_line in code.splitlines():
        line = _strip_comment(raw_line).rstrip()
        if not line.strip():
            continue
        if match := _EXTENDS.match(line):
            add(3, f"Was bedeutet extends {match.group(1)}?")
        elif match := _FUNC.match(line):
            add(0, f"Was bedeutet {match.group(1)}?")
        elif match := _VAR.match(line):
            add(2, f"Wofür ist die Variable {match.group(1)}?")
        elif match := _ASSIGN.match(line):
            statement = f"{match.group(1)} {match.group(2)} {match.group(3)}"
            if len(statement) <= 60:
                add(0, f"Was macht {statement}?")
        elif line.strip().startswith(("if ", "elif ", "else")):
            add(1, "Wann wird dieser if-Teil ausgeführt?")
        if not _FUNC.match(line):
            for call in _CALL.findall(line):
                if call not in _KEYWORDS:
                    add(0, f"Wofür ist {call}()?")
    found.sort(key=lambda item: item[0])  # stable: keeps the order inside the code
    return [question for _, question in found[:limit]]
