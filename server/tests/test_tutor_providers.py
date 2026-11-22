"""Provider switch, health and session access."""

from __future__ import annotations

import pytest
from django.test import Client
from learnharness_protocol import ErrorMessage, HealthStatus, LearningResponse, StudentMessage
from tutor_helpers import ScriptedProvider

from tutor import engine, providers
from tutor.models import AiSettings, TutorSession

pytestmark = pytest.mark.django_db


def test_provider_switch_and_missing_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = AiSettings.load()
    settings.provider = AiSettings.Provider.VLLM
    settings.vllm_model = ""
    with pytest.raises(providers.ProviderError, match="kein Modell"):
        providers.get_provider(settings)
    settings.vllm_model = "qwen"
    vllm = providers.get_provider(settings)
    assert isinstance(vllm, providers.OpenAICompatibleProvider)
    assert str(vllm.client.base_url).startswith("http://localhost:8001/v1")
    assert vllm._limit() == {"max_tokens": settings.max_output_tokens}

    settings.provider = AiSettings.Provider.ANTHROPIC
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(providers.ProviderError, match="ANTHROPIC_API_KEY"):
        providers.get_provider(settings)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    claude = providers.get_provider(settings)
    assert isinstance(claude, providers.AnthropicProvider)
    params = claude._params("system", [{"role": "user", "content": "hi"}])
    assert params["model"] == "claude-opus-5-5"
    assert params["output_config"] == {"effort": "low"}
    assert params["fallbacks"] == "default"

    settings.provider = AiSettings.Provider.OPENAI
    settings.openai_model = "ein-modell"
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    openai_provider = providers.get_provider(settings)
    assert openai_provider._limit() == {  # type: ignore[attr-defined]
        "max_completion_tokens": settings.max_output_tokens
    }


def test_parse_json_accepts_fenced_json() -> None:
    assert providers.parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    with pytest.raises(providers.ProviderError):
        providers.parse_json("kein json")


def test_health_needs_no_token(client: Client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tutor.api.model_available", lambda: (True, 12))
    status = HealthStatus.model_validate(client.get("/api/v1/health").json())
    assert status.server_ok and status.model_ok and status.latency_ms == 12


def test_session_requires_device_token(client: Client) -> None:
    response = client.post(
        "/api/v1/sessions",
        {
            "project_id": "p",
            "client_version": "1",
            "student_profile_id": "x" * 32,
            "student_pseudonym": "Fuchs",
            "experience_level": 0,
        },
        content_type="application/json",
    )
    assert response.status_code == 401


def test_rate_limit(session: TutorSession, scripted: dict[str, ScriptedProvider]) -> None:
    settings = AiSettings.load()
    settings.requests_per_minute = 1
    settings.save()
    scripted["provider"] = ScriptedProvider(chunks=["Hallo!"])
    message = StudentMessage(session_id=session.id, project_id="spiel", message="Hi")
    assert isinstance(engine.Tutor(session).handle(message), LearningResponse)
    limited = engine.Tutor(session).handle(message)
    assert isinstance(limited, ErrorMessage) and limited.code == "rate_limited"


def test_unreachable_model_gives_a_child_friendly_error(
    session: TutorSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(settings: AiSettings | None = None) -> providers.Provider:
        raise providers.ProviderError("kein Modell")

    monkeypatch.setattr(engine, "get_provider", fail)
    message = StudentMessage(session_id=session.id, project_id="spiel", message="Hi")
    result = engine.Tutor(session).handle(message)
    assert isinstance(result, ErrorMessage) and result.code == "model_unavailable"
