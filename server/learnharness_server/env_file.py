"""Reads server/.env when the server runs without Docker (Docker passes it in by itself)."""

from __future__ import annotations

import os
from pathlib import Path


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
        if name and value:
            os.environ.setdefault(name, value)
