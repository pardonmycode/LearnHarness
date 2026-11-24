"""Finds the error of a finished program and removes private paths from it."""

from __future__ import annotations

import re
from pathlib import Path

MAX_ERROR_CHARS = 2000
MAX_GODOT_ERRORS = 4
_TRACEBACK = "Traceback (most recent call last):"
_FILE_LINE = re.compile(r'^\s*File "', re.MULTILINE)
_ERROR_END = re.compile(r"^\w*(?:Error|Exception)\b")
_GODOT_ERROR = re.compile(r"^(?:SCRIPT )?ERROR:.*(?:\n\s+at:.*)?", re.MULTILINE)


def find_run_error(output: str, *, is_python: bool, exit_code: int) -> str | None:
    """Only the error itself: normal program output can contain anything."""
    if not is_python:
        errors = _GODOT_ERROR.findall(output)
        return "\n".join(errors[-MAX_GODOT_ERRORS:])[-MAX_ERROR_CHARS:] if errors else None
    if exit_code == 0:
        return None
    start = output.rfind(_TRACEBACK)
    if start < 0:  # a syntax error has no traceback header
        match = _FILE_LINE.search(output)
        lines = output.strip().splitlines()
        if match is None or not lines or not _ERROR_END.match(lines[-1]):
            return None
        start = match.start()
    return output[start:].strip()[-MAX_ERROR_CHARS:]


def hide_private_paths(text: str, project_root: Path) -> str:
    """Folder names can contain a child's real name; they never go to the AI."""
    replacements: dict[str, str] = {}
    for root, short in ((project_root, "."), (Path.home(), "~")):
        for path in (root, root.resolve()):
            replacements.setdefault(str(path), short)
            replacements.setdefault(path.as_posix(), short)
    for prefix in sorted(replacements, key=len, reverse=True):
        if len(prefix) > 1:
            text = re.sub(re.escape(prefix), replacements[prefix], text, flags=re.IGNORECASE)
    return text
