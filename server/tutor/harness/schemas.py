"""JSON formats the AI must answer in."""

from __future__ import annotations

from typing import Any

from .learn_levels import LEVEL_KINDS
from .rules import SKILLS
from .topics import MISSION_TOPICS, STAGE_KINDS

_STR = {"type": "string"}


def _obj(properties: dict[str, Any]) -> dict[str, Any]:
    # Strict structured output: every property required, nothing else allowed.
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


EXERCISE_SCHEMA = _obj(
    {
        "message": _STR,
        "skill": {"type": "string", "enum": list(SKILLS)},
        "kind": {"type": "string", "enum": ["multiple_choice", "fill_blanks"]},
        "prompt": _STR,
        "code": _STR,
        "choices": {
            "type": "array",
            "items": _obj({"text": _STR, "correct": {"type": "boolean"}}),
        },
        "blanks": {
            "type": "array",
            "items": _obj({"options": {"type": "array", "items": _STR}, "answer": _STR}),
        },
        "explanation_after_correct": _STR,
        "new_file_content": _STR,
    }
)


def mission_exercise_schema(stage: int, topic: str | None) -> dict[str, Any]:
    """The exercise format of one stage, so the AI cannot pick another kind of exercise."""
    properties = dict(EXERCISE_SCHEMA["properties"])
    properties["kind"] = {"type": "string", "enum": [STAGE_KINDS[stage]]}
    properties["skill"] = {"type": "string", "enum": [topic] if topic else list(MISSION_TOPICS)}
    if stage == 3:
        properties["blanks"] = {
            "type": "array",
            "items": _obj({"answer": _STR, "alternatives": {"type": "array", "items": _STR}}),
        }
    return _obj(properties)


MISSION_SCHEMA = _obj(
    {
        "title": _STR,
        "goal": _STR,
        "message": _STR,
        "skill": {"type": "string", "enum": list(MISSION_TOPICS)},
        "steps": {
            "type": "array",
            "items": _obj(
                {
                    "title": _STR,
                    "kind": {"type": "string", "enum": ["understand", "learn", "exercise", "try"]},
                }
            ),
        },
    }
)


PROJECT_PLAN_SCHEMA = _obj(
    {
        "message": _STR,
        "description": _STR,
        "ready": {"type": "boolean"},
    }
)


def learn_exercise_schema(level: int) -> dict[str, Any]:
    """The exercise format of one LearnAgent level."""
    kind = LEVEL_KINDS[level]
    properties = dict(EXERCISE_SCHEMA["properties"])
    properties["kind"] = {"type": "string", "enum": [kind]}
    if kind == "text_blanks":
        properties["blanks"] = {
            "type": "array",
            "items": _obj({"answer": _STR, "alternatives": {"type": "array", "items": _STR}}),
        }
    if kind in ("ordering", "find_bug"):
        for unused in ("code", "choices", "blanks"):
            del properties[unused]
    lines = {"type": "array", "items": _STR}
    if kind == "ordering":
        properties["ordered_lines"] = lines
    if kind == "find_bug":
        properties["buggy_lines"] = lines
        properties["bug_line"] = {"type": "integer"}
    return _obj(properties)


def mission_schema(topics: list[str]) -> dict[str, Any]:
    """The mission format with only these topics to choose from."""
    properties = dict(MISSION_SCHEMA["properties"])
    properties["skill"] = {"type": "string", "enum": topics}
    return _obj(properties)


REVIEW_SCHEMA = _obj(
    {
        "correct": {"type": "boolean"},
        "feedback": _STR,
        "marked_lines": {"type": "array", "items": {"type": "integer"}},
    }
)


EXERCISE_FORMAT_HELP = """Antworte als JSON. "message": kurzer Text an das Kind (ohne Lösung).
"kind": "multiple_choice" oder "fill_blanks". "prompt": die Aufgabe. "code": Code zur Aufgabe
(bei fill_blanks mit Lücken {{1}}, {{2}} …; sonst darf er leer sein). Bei multiple_choice
"choices" mit genau einer richtigen Antwort (correct=true) und "blanks" leer. Bei fill_blanks
"blanks" in der Reihenfolge der Lücken, je mit 2–4 "options" und der richtigen "answer" (muss in
den options stehen), "choices" leer. "explanation_after_correct": was das Kind nach der richtigen
Antwort liest."""
