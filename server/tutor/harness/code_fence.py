"""Markdown code fences belong in chat texts, never into a child's script."""

from __future__ import annotations

_FENCE = "```"


def unwrap_code_fence(text: str) -> str:
    """Remove one fence around the whole text; anything else stays as it is."""
    lines = text.strip().splitlines()
    if len(lines) >= 2 and lines[0].lstrip().startswith(_FENCE) and lines[-1].strip() == _FENCE:
        return "\n".join(lines[1:-1]) + "\n"
    return text


def has_stray_fence(text: str, before: str) -> bool:
    """True when the code has a fence line the child's script did not already contain."""
    known = {line.strip() for line in before.splitlines()}
    return any(
        line.lstrip().startswith(_FENCE) and line.strip() not in known for line in text.splitlines()
    )
