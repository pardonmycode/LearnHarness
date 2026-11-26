"""Reads the AI keys and allowed host names from server/.env when running without Docker."""

from __future__ import annotations

import os
from pathlib import Path

# Only these: the file also holds Docker values such as POSTGRES_HOST=db, which do not
# exist outside Docker. Docker passes the whole file in by itself.
AI_KEYS = frozenset({"ANTHROPIC_API_KEY", "OPENAI_API_KEY", "VLLM_API_KEY"})
# Means the same with and without Docker, e.g. runserver 0.0.0.0:8000 in the home network.
LOCAL_KEYS = AI_KEYS | {"DJANGO_ALLOWED_HOSTS"}


def load_env_file(path: Path) -> None:
    """Real environment variables always win over the file."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.removeprefix("export ").split("=", 1)
        name, value = name.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        # An empty line like "ANTHROPIC_API_KEY=" in the template sets nothing.
        if name in LOCAL_KEYS and value:
            os.environ.setdefault(name, value)
