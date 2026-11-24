"""What the test stand remembers and where its data lives (outside the repository)."""

from __future__ import annotations

import contextlib
import json
import os
import secrets
from dataclasses import asdict, dataclass, field
from pathlib import Path

DATA_DIR = Path.home() / ".learnharness-teststand"
KEY_FIELDS = ("anthropic_key", "vllm_key")


@dataclass
class TeststandConfig:
    provider: str = "anthropic"  # "anthropic" or "vllm"
    anthropic_key: str = ""
    anthropic_model: str = "claude-opus-5-5"
    anthropic_effort: str = "low"
    vllm_url: str = "http://localhost:8001/v1"
    vllm_model: str = ""
    vllm_key: str = ""
    remember_keys: bool = False
    admin_password: str = field(default_factory=lambda: secrets.token_urlsafe(12))

    @property
    def model(self) -> str:
        return self.anthropic_model if self.provider == "anthropic" else self.vllm_model

    def problem(self) -> str | None:
        """What is missing before the stand can start, in plain words."""
        if not self.model.strip():
            return "Bitte trage einen Modellnamen ein."
        claude_key = self.anthropic_key.strip() or os.environ.get("ANTHROPIC_API_KEY")
        if self.provider == "anthropic" and not claude_key:
            return "Bitte trage deinen Claude-API-Schlüssel ein."
        if self.provider == "vllm" and not self.vllm_url.strip():
            return "Bitte trage die Adresse deines vLLM-Servers ein."
        return None


def config_file(data_dir: Path = DATA_DIR) -> Path:
    return data_dir / "teststand.json"


def load(data_dir: Path = DATA_DIR) -> TeststandConfig:
    config = TeststandConfig()
    try:
        data = json.loads(config_file(data_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return config
    if isinstance(data, dict):
        for name, value in data.items():
            if hasattr(config, name) and isinstance(value, type(getattr(config, name))):
                setattr(config, name, value)
    return config


def save(config: TeststandConfig, data_dir: Path = DATA_DIR) -> None:
    """Keys are only written when asked for, and the file is readable by this user only."""
    data = asdict(config)
    if not config.remember_keys:
        for name in KEY_FIELDS:
            data[name] = ""
    data_dir.mkdir(parents=True, exist_ok=True)
    path = config_file(data_dir)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    # Windows keeps the file in the user's own profile anyway.
    with contextlib.suppress(OSError):
        os.chmod(path, 0o600)


def server_environment(config: TeststandConfig, data_dir: Path = DATA_DIR) -> dict[str, str]:
    """Keys go to the local server process only, never into a database or the command line."""
    env = {
        "DJANGO_SETTINGS_MODULE": "learnharness_server.teststand_settings",
        "DJANGO_DEBUG": "1",
        "DJANGO_SECRET_KEY": secrets.token_urlsafe(32),
        "TESTSTAND_DB": str(data_dir / "server.sqlite3"),
        "PYTHONUNBUFFERED": "1",
    }
    if config.anthropic_key.strip():
        env["ANTHROPIC_API_KEY"] = config.anthropic_key.strip()
    if config.vllm_key.strip():
        env["VLLM_API_KEY"] = config.vllm_key.strip()
    return env


def prepare_arguments(config: TeststandConfig) -> list[str]:
    arguments = [
        f"--provider={config.provider}",
        f"--model={config.model.strip()}",
        f"--admin-password={config.admin_password}",
    ]
    if config.provider == "anthropic":
        arguments.append(f"--effort={config.anthropic_effort}")
    else:
        arguments.append(f"--vllm-url={config.vllm_url.strip()}")
    return arguments
