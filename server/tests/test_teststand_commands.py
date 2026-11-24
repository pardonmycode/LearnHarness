"""The commands that set up and check the local test stand."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from tutor.management.commands import teststand_check
from tutor.models import AiSettings

pytestmark = pytest.mark.django_db


def test_prepare_sets_the_ai_and_an_admin() -> None:
    call_command(
        "teststand_prepare",
        "--provider=vllm",
        "--model=qwen",
        "--vllm-url=http://127.0.0.1:9/v1",
        "--admin-password=geheim123",
    )
    settings = AiSettings.load()
    assert settings.provider == "vllm" and settings.vllm_model == "qwen"
    assert settings.vllm_base_url == "http://127.0.0.1:9/v1" and settings.log_prompts
    admin = get_user_model().objects.get(username="teststand")
    assert admin.is_superuser and admin.check_password("geheim123")
    call_command(
        "teststand_prepare", "--provider=anthropic", "--model=claude-x", "--admin-password=neu"
    )
    settings = AiSettings.load()
    assert settings.provider == "anthropic" and settings.anthropic_model == "claude-x"
    assert get_user_model().objects.get(username="teststand").check_password("neu")


class _Provider:
    def __init__(self, answer: bool) -> None:
        self.answer = answer

    def ping(self) -> bool:
        return self.answer


def test_check_reports_the_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    call_command("teststand_prepare", "--provider=vllm", "--model=m", "--admin-password=x")
    monkeypatch.setattr(teststand_check, "get_provider", lambda settings: _Provider(True))
    call_command("teststand_check")
    monkeypatch.setattr(teststand_check, "get_provider", lambda settings: _Provider(False))
    with pytest.raises(CommandError, match="Stimmen Adresse und Modellname"):
        call_command("teststand_check")
