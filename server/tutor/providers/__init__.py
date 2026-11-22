"""AI providers behind one small interface: local vLLM, ChatGPT (OpenAI) and Claude (Anthropic).

vLLM serves the OpenAI-compatible API, so vLLM and ChatGPT share the ``openai`` SDK with
different base URLs. Claude uses the official ``anthropic`` SDK. Which one answers is chosen in
the admin (``AiSettings``); keys come from the environment only.
"""

from __future__ import annotations

import time

from django.core.cache import cache

from ..models import AiSettings
from .anthropic_provider import FALLBACK_BETA, FALLBACK_MODELS, AnthropicProvider
from .base import Message, Provider, ProviderError, Usage, parse_json
from .openai_provider import OpenAICompatibleProvider

__all__ = [
    "AnthropicProvider",
    "FALLBACK_BETA",
    "FALLBACK_MODELS",
    "Message",
    "OpenAICompatibleProvider",
    "PING_CACHE_SECONDS",
    "Provider",
    "ProviderError",
    "Usage",
    "get_provider",
    "model_available",
    "parse_json",
]


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
