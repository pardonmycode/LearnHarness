"""The answer format and checks of the tab "Code verstehen"."""

from __future__ import annotations

import re
from typing import Any

from .topics import MAX_EXERCISE_CODE_LINES

MIN_COPIED_ANSWER = 10  # shorter answers may appear in an explanation by chance

EXPLAIN_FORMAT_HELP = f"""Antworte als JSON. "message": deine Erklärung und die Antwort auf die
Frage des Kindes. "skill": das Thema, um das es im Code geht. "kind": "multiple_choice". "prompt":
die Verständnisfrage. "code": ein kurzer veränderter Codeausschnitt (höchstens
{MAX_EXERCISE_CODE_LINES} Zeilen) oder leer. "choices": 2 bis 4 Möglichkeiten, genau eine mit
correct=true. "explanation_after_correct": was das Kind nach der richtigen Antwort liest."""


def _squeezed(text: str) -> str:
    return re.sub(r"\s+", "", text).casefold()


def check_explanation(exercise: Any, answers: dict[str, Any], message: str) -> str | None:
    """A reason when the explanation is missing or the question can simply be copied."""
    if not message.strip():
        return "Die Erklärung in message fehlt"
    if len(str(exercise.code or "").splitlines()) > MAX_EXERCISE_CODE_LINES:
        return f"Der Code der Frage hat mehr als {MAX_EXERCISE_CODE_LINES} Zeilen"
    right = next(choice.text for choice in exercise.choices if choice.id == answers["choice"])
    answer = _squeezed(right)
    if len(answer) >= MIN_COPIED_ANSWER and answer in _squeezed(message):
        return "Die richtige Antwort steht wörtlich in der Erklärung"
    return None
