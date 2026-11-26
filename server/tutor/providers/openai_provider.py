"""vLLM and ChatGPT through the OpenAI-compatible API."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..models import AiSettings
from .base import Message, Provider, ProviderError, Usage


class OpenAICompatibleProvider(Provider):
    def __init__(
        self,
        provider: str,
        model: str,
        max_tokens: int,
        base_url: str | None,
        api_key: str,
        *,
        timeout: float = 90,
    ) -> None:
        super().__init__(provider, model, max_tokens)
        import openai

        self._openai = openai
        # vLLM accepts any key unless started with --api-key.
        self.client = openai.OpenAI(
            base_url=base_url, api_key=api_key or "EMPTY", timeout=timeout, max_retries=1
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

    def first_model(self) -> str | None:
        """The first model the server offers; a local vLLM usually serves exactly one."""
        try:
            return next((item.id for item in self.client.models.list() if item.id), None)
        except self._openai.APIError:
            return None

    def ping(self) -> bool:
        try:
            if self.provider == AiSettings.Provider.VLLM:
                return any(item.id == self.model for item in self.client.models.list())
            self.client.models.retrieve(self.model)
            return True
        except self._openai.APIError:
            return False
