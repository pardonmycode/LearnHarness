"""Read recent errors from Godot's runtime log (only if file logging is enabled)."""

from __future__ import annotations

import os
import re
from pathlib import Path

from .output_parser import GodotMessage, parse_godot_output
from .paths import godot_data_dir

TAIL_BYTES = 128 * 1024
_UNSAFE = re.compile(r'[<>:"/\\|?*]')


def default_log_path(project_name: str, data_dir: Path | None = None) -> Path | None:
    """``<Godot-Datenordner>/app_userdata/<Projekt>/logs/godot.log`` on every system."""
    base = data_dir if data_dir is not None else godot_data_dir()
    if base is None:
        return None
    # Godot replaces characters that are not allowed in folder names (on every system).
    folder = _UNSAFE.sub("_", project_name).strip() or "[unnamed project]"
    return base / "app_userdata" / folder / "logs" / "godot.log"


def read_recent_errors(log_path: Path, limit: int = 20) -> list[GodotMessage]:
    """Parse only the end of the log; returns the newest ``limit`` messages."""
    with log_path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - TAIL_BYTES))
        data = handle.read()
    text = data.decode("utf-8", errors="replace")
    return parse_godot_output(text)[-limit:]
