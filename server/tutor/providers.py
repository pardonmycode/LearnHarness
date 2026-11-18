"""AI providers behind one small interface: local vLLM, ChatGPT (OpenAI) and Claude (Anthropic).

vLLM serves the OpenAI-compatible API, so vLLM and ChatGPT share the ``openai`` SDK with
different base URLs. Claude uses the official ``anthropic`` SDK. Which one answers is chosen in
the admin (``AiSettings``); keys come from the environment only.
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from django.core.cache import cache

from .models import AiSettings

Message = dict[str, str]  # {"role": "user" | "assistant", "content": "..."}

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


class OpenAICompatibleProvider(Provider):
    def __init__(
        self, provider: str, model: str, max_tokens: int, base_url: str | None, api_key: str
    ) -> None:
        super().__init__(provider, model, max_tokens)
        import openai

        self._openai = openai
        # vLLM accepts any key unless started with --api-key.
        self.client = openai.OpenAI(
            base_url=base_url, api_key=api_key or "EMPTY", timeout=90, max_retries=1
        )

    def _limit(self) -> dict[str, int]:
        # Current OpenAI models take max_completion_tokens; vLLM still documents max_tokens.
        if self.provider == AiSettings.Provider.OPENAI:
            return {"max_completion_tokens": self.max_tokens}
        return {"max_tokens": self.max_tokens}

    def stream(self, system: str, messages: list[Message]) -> Iterator[str]:
        try:
            chunks = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, *messages],  # type: ignore[list-item]
                stream=True,
                stream_options={"include_usage": True},
                **self._limit(),  # type: ignore[arg-type]
            )
            for chunk in chunks:
                if chunk.usage is not None:
                    self.usage = Usage(chunk.usage.prompt_tokens, chunk.usage.completion_tokens)
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except self._openai.APIError as exc:
            raise ProviderError(f"{type(exc).__name__}: {exc}") from exc

    def complete_json(self, system: str, messages: list[Message], schema: dict[str, Any]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, *messages],  # type: ignore[list-item]
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "antwort", "schema": schema, "strict": True},
                },
                **self._limit(),  # type: ignore[arg-type]
            )
        except self._openai.APIError as exc:
            raise ProviderError(f"{type(exc).__name__}: {exc}") from exc
        if response.usage is not None:
            self.usage = Usage(response.usage.prompt_tokens, response.usage.completion_tokens)
        choice = response.choices[0] if response.choices else None
        if choice is None or not choice.message.content:
            raise ProviderError("Leere Antwort")
        if choice.finish_reason == "length":
            raise ProviderError("Antwort abgeschnitten (Höchstlänge erreicht)")
        return choice.message.content

    def ping(self) -> bool:
        try:
            if self.provider == AiSettings.Provider.VLLM:
                return any(item.id == self.model for item in self.client.models.list())
            self.client.models.retrieve(self.model)
            return True
        except self._openai.APIError:
            return False


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


def get_provider(settings: AiSettings | None = None) -> Provider:
    settings = settings or AiSettings.load()
    model = settings.active_model
    if not model:
        raise ProviderError("Für den aktiven Anbieter ist kein Modell eingetragen.")
    key = AiSettings.api_key(settings.provider)
    if settings.provider == AiSettings.Provider.ANTHROPIC:
        if not key:
            raise ProviderError("ANTHROPIC_API_KEY fehlt in server/.env.")
        return AnthropicProvider(model, settings.max_output_tokens, key, settings.anthropic_effort)
    if settings.provider == AiSettings.Provider.OPENAI:
        if not key:
            raise ProviderError("OPENAI_API_KEY fehlt in server/.env.")
        return OpenAICompatibleProvider(
            settings.provider, model, settings.max_output_tokens, None, key
        )
    return OpenAICompatibleProvider(
        settings.provider, model, settings.max_output_tokens, settings.vllm_base_url, key
    )


PING_CACHE_SECONDS = 60


def model_available(force: bool = False) -> tuple[bool, int | None]:
    """Is the active model reachable? Cached, because the app asks every few seconds."""
    settings = AiSettings.load()
    key = f"tutor:ping:{settings.provider}:{settings.active_model}:{settings.updated_at}"
    cached = None if force else cache.get(key)
    if cached is not None:
        return tuple(cached)  # type: ignore[return-value]
    started = time.monotonic()
    try:
        ok = get_provider(settings).ping()
    except ProviderError:
        ok = False
    result = (ok, int((time.monotonic() - started) * 1000))
    cache.set(key, list(result), PING_CACHE_SECONDS)
    return result


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
