"""Claude through the Anthropic API."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..models import AiSettings
from .base import Message, Provider, ProviderError, Usage

# Claude models that support the server-side refusal fallback (routes a declined request to
# another model inside the same call). Other models are called without it.
FALLBACK_MODELS = frozenset(
    {
        "claude-fable-5-2",
        "claude-fable-5-1",
        "claude-opus-5-5",
        "claude-opus-5",
        "claude-sonnet-5-5",
    }
)


FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AnthropicProvider(Provider):
    def __init__(self, model: str, max_tokens: int, api_key: str, effort: str) -> None:
        super().__init__(AiSettings.Provider.ANTHROPIC, model, max_tokens)
        import anthropic

        self._anthropic = anthropic
        self.client = anthropic.Anthropic(api_key=api_key or None, timeout=90, max_retries=1)
        self.effort = effort

    def _params(self, system: str, messages: list[Message]) -> dict[str, Any]:
        params: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": messages,
        }
        if self.effort:
            params["output_config"] = {"effort": self.effort}
        if self.model in FALLBACK_MODELS:
            params["betas"] = [FALLBACK_BETA]
            params["fallbacks"] = "default"
        return params

    def _check(self, message: Any) -> None:
        self.usage = Usage(message.usage.input_tokens, message.usage.output_tokens)
        if message.stop_reason == "refusal":
            raise ProviderError("Claude hat die Anfrage abgelehnt (refusal)")
        if message.stop_reason == "max_tokens":
            raise ProviderError("Antwort abgeschnitten (Höchstlänge erreicht)")

    def stream(self, system: str, messages: list[Message]) -> Iterator[str]:
        params = self._params(system, messages)
        try:
            if "betas" in params:
                manager = self.client.beta.messages.stream(**params)
            else:
                manager = self.client.messages.stream(**params)
            with manager as stream:
                yield from stream.text_stream
                self._check(stream.get_final_message())
        except self._anthropic.APIError as exc:
            raise ProviderError(f"{type(exc).__name__}: {exc}") from exc

    def complete_json(self, system: str, messages: list[Message], schema: dict[str, Any]) -> str:
        params = self._params(system, messages)
        params["output_config"] = {
            **params.get("output_config", {}),
            "format": {"type": "json_schema", "schema": schema},
        }
        try:
            if "betas" in params:
                message = self.client.beta.messages.create(**params)
            else:
                message = self.client.messages.create(**params)
        except self._anthropic.APIError as exc:
            raise ProviderError(f"{type(exc).__name__}: {exc}") from exc
        self._check(message)
        text = next((block.text for block in message.content if block.type == "text"), "")
        if not text:
            raise ProviderError("Leere Antwort")
        return text

    def ping(self) -> bool:
        try:
            self.client.models.retrieve(self.model)
            return True
        except self._anthropic.APIError:
            return False
