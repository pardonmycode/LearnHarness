"""Projects that the local Godot project manager already knows."""

from __future__ import annotations

import os
import re
from pathlib import Path

# Godot 4: %APPDATA%/Godot/projects.cfg, one ConfigFile section per project: ["C:/path"]
_SECTION = re.compile(r'^\s*\[\s*"((?:[^"\\]|\\.)*)"\s*\]\s*$')
# Godot 3: editor_settings-3.tres, lines like projects/name = "C:/path"
_GODOT3_ENTRY = re.compile(r'^\s*projects/[^=]+=\s*"((?:[^"\\]|\\.)*)"\s*$')
_MAX_BYTES = 1024 * 1024


def _unescape(value: str) -> str:
    return re.sub(r"\\(.)", lambda match: match.group(1), value)


def _read(path: Path) -> str:
    try:
        if not path.is_file() or path.stat().st_size > _MAX_BYTES:
            return ""
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def parse_project_paths(text: str, pattern: re.Pattern[str] = _SECTION) -> list[str]:
    return [
        _unescape(match.group(1)) for line in text.splitlines() if (match := pattern.match(line))
    ]


def known_godot_projects(appdata: str | None = None) -> list[Path]:
    """Existing project folders from Godot's project list, in file order, without duplicates."""
    base = appdata if appdata is not None else os.environ.get("APPDATA", "")
    if not base:
        return []
    godot_dir = Path(base) / "Godot"
    candidates = parse_project_paths(_read(godot_dir / "projects.cfg"))
    candidates += parse_project_paths(_read(godot_dir / "editor_settings-3.tres"), _GODOT3_ENTRY)
    found: list[Path] = []
    seen: set[str] = set()
    for raw in candidates:
        if not raw.strip():
            continue
        try:
            folder = Path(raw)
            if not (folder / "project.godot").is_file():
                continue
            key = os.path.normcase(str(folder.resolve()))
        except (OSError, ValueError):
            continue
        if key in seen:
            continue
        seen.add(key)
        found.append(folder)
    return found
