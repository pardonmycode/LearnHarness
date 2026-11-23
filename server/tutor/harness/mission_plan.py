"""Checks the plan of a mission before a child gets to see it."""

from __future__ import annotations

import re
from typing import Any

from .checks import HarnessRejected

MIN_STEPS = 3
MAX_STEPS = 5
_KINDS = {"understand", "learn", "exercise", "try"}
# Only clear code signs: a title like "return nutzen" is fine German for a child.
_CODE_SIGNS = re.compile(r"[`=(){}\[\]]")


def _plain(text: Any, what: str) -> str:
    clean = " ".join(str(text or "").split())
    if not clean:
        raise HarnessRejected(f"{what} fehlt")
    if _CODE_SIGNS.search(clean):
        raise HarnessRejected(f"{what} darf keinen Code enthalten")
    return clean


def check_mission_plan(
    data: dict[str, Any], topics: list[str], try_title: str
) -> list[dict[str, str]]:
    """The checked steps, ending in exactly one try step."""
    if data.get("skill") not in topics:
        raise HarnessRejected(f"Thema muss eines von diesen sein: {', '.join(topics)}")
    _plain(data.get("title"), "Titel")
    _plain(data.get("goal"), "Ziel")
    steps = [
        {"title": _plain(step.get("title"), "Schritttitel"), "kind": str(step.get("kind"))}
        for step in data.get("steps") or []
    ]
    if any(step["kind"] not in _KINDS for step in steps):
        raise HarnessRejected("Unbekannte Schrittart")
    if not steps or steps[-1]["kind"] != "try":
        steps.append({"title": try_title, "kind": "try"})
    if not MIN_STEPS <= len(steps) <= MAX_STEPS:
        raise HarnessRejected(f"Mission braucht {MIN_STEPS} bis {MAX_STEPS} Schritte")
    if any(step["kind"] == "try" for step in steps[:-1]):
        raise HarnessRejected('Nur der letzte Schritt darf "try" sein')
    if not any(step["kind"] == "exercise" for step in steps):
        raise HarnessRejected('Mission braucht mindestens einen Schritt "exercise"')
    return steps
