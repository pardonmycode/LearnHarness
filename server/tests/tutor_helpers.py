"""Shared helpers of the tutor tests."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from tutor import providers

PLAYER = "extends CharacterBody2D\n\nvar speed = 200\n"


class ScriptedProvider(providers.Provider):
    """Answers from a script and remembers what it was asked."""

    def __init__(self, *, chunks: list[str] | None = None, json_answers: list[Any] = ()) -> None:
        super().__init__("vllm", "test-modell", 1000)
        self.chunks = chunks or []
        self.json_answers = list(json_answers)
        self.calls: list[tuple[str, list[providers.Message]]] = []

    def stream(self, system: str, messages: list[providers.Message]) -> Iterator[str]:
        self.calls.append((system, messages))
        self.usage = providers.Usage(10, 5)
        yield from self.chunks

    def complete_json(
        self, system: str, messages: list[providers.Message], schema: dict[str, Any]
    ) -> str:
        self.calls.append((system, messages))
        self.usage = providers.Usage(20, 8)
        answer = self.json_answers.pop(0)
        return answer if isinstance(answer, str) else json.dumps(answer)

    def ping(self) -> bool:
        return True


def _headers(token: str) -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def _exercise_json(**overrides: Any) -> dict[str, Any]:
    data = {
        "message": "Damit die Figur springt, braucht sie eine Sprungkraft.",
        "skill": "variables",
        "kind": "fill_blanks",
        "prompt": "Womit legst du eine neue Variable an?",
        "code": "{{1}} jump_force = 400",
        "choices": [],
        "blanks": [{"options": ["var", "func", "if"], "answer": "var"}],
        "explanation_after_correct": "Genau: var legt eine Variable an.",
        "new_file_content": PLAYER + "# Wie stark die Figur springt\nvar jump_force = 400\n",
    }
    data.update(overrides)
    return data
