"""The test stand keeps keys out of files unless asked and never puts them on a command line."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from learnharness_client.teststand import config as stand_config
from learnharness_client.teststand.config import TeststandConfig


def test_keys_are_only_saved_when_asked(tmp_path: Path) -> None:
    config = TeststandConfig(anthropic_key="sk-ant-geheim", vllm_model="qwen")
    stand_config.save(config, tmp_path)
    saved = json.loads(stand_config.config_file(tmp_path).read_text(encoding="utf-8"))
    assert saved["anthropic_key"] == "" and saved["vllm_model"] == "qwen"
    config.remember_keys = True
    stand_config.save(config, tmp_path)
    assert stand_config.load(tmp_path).anthropic_key == "sk-ant-geheim"
    if sys.platform != "win32":
        assert os.stat(stand_config.config_file(tmp_path)).st_mode & 0o777 == 0o600


def test_damaged_file_gives_defaults(tmp_path: Path) -> None:
    stand_config.config_file(tmp_path).write_text('{"provider": 3, "vllm_model": "m"', "utf-8")
    assert stand_config.load(tmp_path).provider == "anthropic"
    stand_config.config_file(tmp_path).write_text('{"provider": 3, "vllm_model": "m"}', "utf-8")
    loaded = stand_config.load(tmp_path)
    assert loaded.provider == "anthropic" and loaded.vllm_model == "m"


def test_key_goes_into_the_environment_not_the_arguments(tmp_path: Path) -> None:
    config = TeststandConfig(anthropic_key="sk-ant-geheim")
    env = stand_config.server_environment(config, tmp_path)
    arguments = stand_config.prepare_arguments(config)
    assert env["ANTHROPIC_API_KEY"] == "sk-ant-geheim"
    assert env["TESTSTAND_DB"] == str(tmp_path / "server.sqlite3")
    assert env["DJANGO_SETTINGS_MODULE"].endswith("teststand_settings")
    assert not any("geheim" in argument for argument in arguments)
    vllm = TeststandConfig(provider="vllm", vllm_model="qwen", vllm_url="http://h:8001/v1")
    assert "--vllm-url=http://h:8001/v1" in stand_config.prepare_arguments(vllm)
    assert "--model=qwen" in stand_config.prepare_arguments(vllm)
    empty = TeststandConfig(provider="vllm", vllm_model="")
    assert not any(a.startswith("--model") for a in stand_config.prepare_arguments(empty))
    assert "ANTHROPIC_API_KEY" not in stand_config.server_environment(vllm, tmp_path)


@pytest.mark.parametrize(
    ("config", "problem"),
    [
        (TeststandConfig(provider="vllm", vllm_model=""), None),
        (TeststandConfig(provider="anthropic", anthropic_model=""), "Modellnamen"),
        (TeststandConfig(provider="vllm", vllm_model="m", vllm_url=""), "Adresse"),
        (TeststandConfig(provider="vllm", vllm_model="m"), None),
        (TeststandConfig(anthropic_key="k"), None),
    ],
)
def test_missing_input_is_named(config: TeststandConfig, problem: str | None) -> None:
    found = config.problem()
    assert (found is None) if problem is None else (problem in (found or ""))


def test_missing_claude_key_is_named(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert "Claude-API-Schlüssel" in (TeststandConfig().problem() or "")
