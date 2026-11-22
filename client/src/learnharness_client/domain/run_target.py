"""Decides what the Start button runs: a Python script of the project or the Godot game."""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from ..texts import T
from .project import Project


class RunNotPossible(ValueError):
    """The message is shown to the child in the terminal."""


@dataclass(frozen=True, slots=True)
class RunTarget:
    program: str
    arguments: tuple[str, ...]
    working_dir: Path
    label: str
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


def script_to_run(project: Project, current: Path | None) -> Path | None:
    """The open script when it is in the project folder, else the project's main.py.

    A file like game/player.py is a building block: the game starts from main.py.
    """
    main = project.root / "main.py"
    if current is not None and current.parent == project.root:
        chosen: Path | None = current
    elif main.is_file():
        chosen = main
    else:
        chosen = current
    return project.guard.ensure_allowed(chosen) if chosen is not None else None


def run_target(project: Project, current: Path | None, godot: str = "") -> RunTarget:
    if project.language == "gdscript":
        if not godot:
            raise RunNotPossible(T.GODOT_NOT_SET)
        return RunTarget(godot, ("--path", str(project.root)), project.root, project.name, False)
    script = script_to_run(project, current)
    if script is None:
        raise RunNotPossible(T.TERMINAL_NO_SCRIPT)
    python = find_python()
    if python is None:
        raise RunNotPossible(T.TERMINAL_NO_PYTHON)
    program, prefix = python
    # -u: prompts from input() and prints appear immediately.
    arguments = (*prefix, "-u", str(script))
    label = script.relative_to(project.root).as_posix()
    return RunTarget(program, arguments, project.root, label, True)
