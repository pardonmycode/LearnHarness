"""The programs the terminal may start: a Python script of the project or the Godot game."""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RunTarget:
    program: str
    arguments: tuple[str, ...]
    working_dir: Path
    project_root: Path
    is_python: bool


def find_python() -> tuple[str, tuple[str, ...]] | None:
    """Program and leading arguments of a Python interpreter, or None."""
    # In the packaged app sys.executable is LearnHarness itself, not Python.
    if not getattr(sys, "frozen", False):
        return sys.executable, ()
    names = ("py", "python", "python3") if sys.platform == "win32" else ("python3", "python")
    for name in names:
        found = shutil.which(name)
        if found:
            return found, ("-3",) if name == "py" else ()
    return None
