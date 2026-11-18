"""Parse Godot console and log output into file/line messages."""

from __future__ import annotations

import re
from dataclasses import dataclass

_ERROR_START = re.compile(
    r"^\s*(?P<kind>SCRIPT ERROR|USER SCRIPT ERROR|ERROR|USER ERROR|Parse Error)\s*:\s*(?P<text>.*)$"
)
_LOCATION = re.compile(r"res://(?P<file>[^:\s()]+\.gd):(?P<line>\d+)", re.IGNORECASE)
# Godot repeats the parse error as "Failed to load script" – that adds no information.
_NOISE = re.compile(r"Failed to load script|Failed loading resource", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class GodotMessage:
    file: str
    line: int
    message: str


def parse_godot_output(text: str) -> list[GodotMessage]:
    """Return one message per error block, using the first ``res://…gd:line`` seen."""
    messages: list[GodotMessage] = []
    current: str | None = None
    location: tuple[str, int] | None = None

    def flush() -> None:
        if current is None:
            return
        file, line = location if location else ("", 0)
        message = GodotMessage(file, line, current)
        if message not in messages:
            messages.append(message)

    for raw_line in text.splitlines():
        start = _ERROR_START.match(raw_line)
        if start:
            flush()
            body = start.group("text").strip()
            if _NOISE.search(body):
                current, location = None, None
                continue
            current = body.removeprefix("Parse Error:").strip() or body
            match = _LOCATION.search(body)
            location = (match.group("file"), int(match.group("line"))) if match else None
            continue
        if current is not None and location is None:
            match = _LOCATION.search(raw_line)
            if match:
                location = (match.group("file"), int(match.group("line")))
    flush()
    return messages
