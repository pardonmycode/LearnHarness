"""Common provider interface and JSON parsing."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

Message = dict[str, str]  # {"role": "user" | "assistant", "content": "..."}


class ProviderError(Exception):
    """The AI could not answer (network, key, refusal, invalid output)."""


@dataclass
class Usage:
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass
class Provider(ABC):
    provider: str
    model: str
    max_tokens: int
    usage: Usage = field(default_factory=Usage)

    @abstractmethod
    def stream(self, system: str, messages: list[Message]) -> Iterator[str]:
        """Yield text pieces; ``self.usage`` is filled when the stream ends."""

    @abstractmethod
    def complete_json(self, system: str, messages: list[Message], schema: dict[str, Any]) -> str:
        """Return JSON text that follows ``schema`` (structured output)."""

    @abstractmethod
    def ping(self) -> bool:
        """Cheap reachability check without generating tokens."""


def parse_json(text: str) -> dict[str, Any]:
    """Some local models wrap JSON in a code fence despite structured output."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[1] if "\n" in stripped else ""
        stripped = stripped.rsplit("```", 1)[0]
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ProviderError("Die KI hat kein gültiges JSON geliefert") from exc
    if not isinstance(data, dict):
        raise ProviderError("Die KI hat kein JSON-Objekt geliefert")
    return data
