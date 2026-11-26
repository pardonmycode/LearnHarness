"""The commands that set up and check the local test stand."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from tutor import providers
from tutor.management.commands import teststand_check, teststand_prepare
from tutor.models import AiSettings

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _no_vllm_server(monkeypatch: pytest.MonkeyPatch) -> None:
    """No real vLLM in tests: the model list is empty unless a test says otherwise."""
    monkeypatch.setattr(providers.OpenAICompatibleProvider, "first_model", lambda self: None)


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
    with pytest.raises(CommandError, match="bietet kein Modell an"):
        call_command("teststand_check")
    monkeypatch.setattr(teststand_check, "adopt_first_model", lambda settings: "m")
    monkeypatch.setattr(teststand_check, "get_provider", lambda settings: _Provider(True))
    call_command("teststand_check")
    monkeypatch.setattr(teststand_check, "get_provider", lambda settings: _Provider(False))
    with pytest.raises(CommandError, match="Stimmen Adresse und Modellname"):
        call_command("teststand_check")


def test_the_first_model_of_vllm_is_taken(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        providers.OpenAICompatibleProvider, "first_model", lambda self: "Qwen/Qwen3-Coder"
    )
    monkeypatch.setattr(teststand_check, "get_provider", lambda settings: _Provider(True))
    call_command("teststand_prepare", "--provider=vllm", "--admin-password=x")
    assert AiSettings.load().vllm_model == "Qwen/Qwen3-Coder"
    settings = AiSettings.load()
    settings.vllm_model = "von-hand"
    settings.save()
    call_command("teststand_check")
    assert AiSettings.load().vllm_model == "Qwen/Qwen3-Coder"


def test_vllm_without_any_model_cannot_be_prepared() -> None:
    with pytest.raises(CommandError, match="Modellnamen"):
        call_command("teststand_prepare", "--provider=vllm", "--admin-password=x")
    assert teststand_prepare.ADMIN_USER == "teststand"


class _Model:
    def __init__(self, model_id: str) -> None:
        self.id = model_id


def test_first_model_reads_the_model_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.undo()  # the real first_model this time, with a fake model list
    provider = providers.OpenAICompatibleProvider("vllm", "", 100, "http://127.0.0.1:9/v1", "")
    monkeypatch.setattr(
        provider.client.models, "list", lambda: [_Model("erstes"), _Model("zweites")]
    )
    assert provider.first_model() == "erstes"
    monkeypatch.setattr(provider.client.models, "list", lambda: [])
    assert provider.first_model() is None
