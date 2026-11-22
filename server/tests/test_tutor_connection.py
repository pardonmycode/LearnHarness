"""The connection test names the real problem; server/.env works without Docker."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import anthropic
import httpx
import pytest
from pytest import MonkeyPatch

from learnharness_server.env_file import load_env_file
from tutor import providers
from tutor.models import AiSettings

pytestmark = pytest.mark.django_db


def _status_error(kind: type[anthropic.APIStatusError], status: int, text: str) -> Exception:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return kind(text, response=httpx.Response(status, request=request), body=None)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (_status_error(anthropic.AuthenticationError, 401, "invalid x-api-key"), "ungültig"),
        (_status_error(anthropic.PermissionDeniedError, 403, "denied"), "keinen Zugriff"),
        (_status_error(anthropic.NotFoundError, 404, "model"), "Modell"),
        (_status_error(anthropic.RateLimitError, 429, "slow"), "Limit"),
        (
            _status_error(anthropic.BadRequestError, 400, "Your credit balance is too low"),
            "Guthaben",
        ),
    ],
)
def test_claude_problems_are_named(
    monkeypatch: MonkeyPatch, error: Exception, expected: str
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-geheim")
    settings = AiSettings.load()
    settings.provider = AiSettings.Provider.ANTHROPIC

    def fail(**_params: Any) -> None:
        raise error

    provider = providers.get_provider(settings)
    monkeypatch.setattr(provider.client.messages, "create", fail)
    monkeypatch.setattr(providers, "get_provider", lambda _settings: provider)
    problem = providers.connection_problem(settings)
    assert problem is not None and expected in problem
    assert "geheim" not in problem


def test_missing_key_is_named(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    settings = AiSettings.load()
    settings.provider = AiSettings.Provider.ANTHROPIC
    assert "ANTHROPIC_API_KEY fehlt" in providers.connection_problem(settings)


def test_env_file_gives_only_ai_keys(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "VLLM_API_KEY", "POSTGRES_HOST"):
        monkeypatch.setenv(name, "platzhalter")
        monkeypatch.delenv(name)
    monkeypatch.setenv("OPENAI_API_KEY", "echt")
    env = tmp_path / ".env"
    env.write_text(
        '# Kommentar\nexport ANTHROPIC_API_KEY="sk-ant-test"\nOPENAI_API_KEY=datei\n'
        "VLLM_API_KEY=\nPOSTGRES_HOST=db\n"
    )
    load_env_file(env)
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-test"
    assert os.environ["OPENAI_API_KEY"] == "echt"
    assert "VLLM_API_KEY" not in os.environ
    assert "POSTGRES_HOST" not in os.environ
