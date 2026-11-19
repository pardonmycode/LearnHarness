"""Where Godot 4 keeps its files on Windows, Linux and macOS.

Godot separates editor settings (incl. ``projects.cfg``) from data such as the
``app_userdata/<Projekt>/logs/godot.log`` of a running game:

* Windows: both in ``%APPDATA%\\Godot``
* Linux: settings in ``$XDG_CONFIG_HOME/godot`` (``~/.config/godot``),
  data in ``$XDG_DATA_HOME/godot`` (``~/.local/share/godot``)
* macOS: both in ``~/Library/Application Support/Godot``
"""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Mapping
from pathlib import Path

# Names under which Godot is usually found on PATH (Linux packages, Flatpak wrappers,
# Windows/macOS when the user added it).
GODOT_COMMANDS = ("godot4", "godot", "Godot", "godot.exe")


def _home(env: Mapping[str, str]) -> Path | None:
    home = env.get("HOME") or env.get("USERPROFILE")
    if home:
        return Path(home)
    try:
        return Path.home()
    except RuntimeError:
        return None


def _xdg(env: Mapping[str, str], variable: str, fallback: str) -> Path | None:
    value = env.get(variable, "").strip()
    # Only used for Linux; relative values are invalid by the XDG spec and ignored.
    if value.startswith("/"):
        return Path(value)
    home = _home(env)
    return home / fallback if home else None


def godot_config_dir(
    env: Mapping[str, str] | None = None, platform: str | None = None
) -> Path | None:
    """Folder with Godot's editor settings and ``projects.cfg``."""
    env = os.environ if env is None else env
    platform = sys.platform if platform is None else platform
    if platform == "win32":
        appdata = env.get("APPDATA", "")
        return Path(appdata) / "Godot" if appdata else None
    if platform == "darwin":
        home = _home(env)
        return home / "Library" / "Application Support" / "Godot" if home else None
    base = _xdg(env, "XDG_CONFIG_HOME", ".config")
    return base / "godot" if base else None


def godot_data_dir(
    env: Mapping[str, str] | None = None, platform: str | None = None
) -> Path | None:
    """Folder that contains ``app_userdata`` (logs and save games of projects)."""
    env = os.environ if env is None else env
    platform = sys.platform if platform is None else platform
    if platform in ("win32", "darwin"):
        return godot_config_dir(env, platform)
    base = _xdg(env, "XDG_DATA_HOME", ".local/share")
    return base / "godot" if base else None


def find_godot_on_path() -> str:
    """Godot from PATH, e.g. after ``apt install godot4`` or ``flatpak`` wrappers; else ""."""
    for name in GODOT_COMMANDS:
        found = shutil.which(name)
        if found:
            return found
    return ""
