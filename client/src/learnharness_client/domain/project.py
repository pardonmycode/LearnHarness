"""Project discovery and metadata for Godot and Python projects."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from ..texts import T
from .path_guard import PathGuard, PathNotAllowed, ProjectLanguage, fold_case

_PROJECT_NAME = re.compile(r'^config/name\s*=\s*"((?:[^"\\]|\\.)*)"\s*$', re.MULTILINE)
_PYTHON_MARKERS = ("pyproject.toml", "requirements.txt", "setup.py")
# Letters (also umlauts), digits, spaces, "_" and "-": safe as a folder name on every system.
_FOLDER_NAME = re.compile(r"^\w(?:[\w -]*[\w-])?$")
_RESERVED_NAMES = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{number}" for number in range(1, 10)}
    | {f"lpt{number}" for number in range(1, 10)}
)
MAX_PROJECT_NAME = 60
PYTHON_MAIN_TEMPLATE = '# Dein erstes Python-Programm.\nprint("Hallo, Welt!")\n'


def _is_python_folder(root: Path) -> bool:
    if any((root / marker).is_file() for marker in _PYTHON_MARKERS):
        return True
    return any(child.is_file() for child in root.glob("*.py"))


def is_project_folder(root: Path) -> bool:
    """True for a folder LearnHarness can open as a Godot or Python project."""
    try:
        return root.is_dir() and ((root / "project.godot").is_file() or _is_python_folder(root))
    except OSError:
        return False


def _project_id(root: Path) -> str:
    # Same id on Windows as before; on Linux "Spiel" and "spiel" are different projects.
    return hashlib.sha256(fold_case(str(root)).encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class Project:
    root: Path
    name: str
    project_id: str
    guard: PathGuard
    language: ProjectLanguage = "gdscript"

    @classmethod
    def open(cls, root: Path | str) -> Project:
        candidate = Path(root).resolve(strict=True)
        descriptor = candidate / "project.godot"
        if descriptor.is_file():
            text = descriptor.read_text(encoding="utf-8-sig", errors="replace")
            match = _PROJECT_NAME.search(text)
            name = match.group(1).replace(r"\"", '"') if match else candidate.name
            return cls(candidate, name, _project_id(candidate), PathGuard(candidate))
        if not candidate.is_dir() or not _is_python_folder(candidate):
            raise PathNotAllowed(T.PROJECT_MISSING_DESCRIPTOR)
        # The whole home folder or drive is no project, even with a stray script in it.
        if candidate == Path.home().resolve() or candidate == Path(candidate.anchor):
            raise PathNotAllowed(T.PROJECT_FOLDER_TOO_BROAD)
        guard = PathGuard(candidate, language="python")
        return cls(candidate, candidate.name, _project_id(candidate), guard, "python")


# Older name, kept for code that only deals with Godot projects.
GodotProject = Project


def create_python_project(parent: Path | str, name: str) -> Project:
    """Create ``parent/name`` with a runnable main.py; never touches an existing folder."""
    clean = name.strip()
    if (
        len(clean) > MAX_PROJECT_NAME
        or not _FOLDER_NAME.fullmatch(clean)
        or clean.casefold() in _RESERVED_NAMES
    ):
        raise PathNotAllowed(T.PROJECT_NAME_INVALID)
    root = Path(parent).resolve(strict=True) / clean
    try:
        root.mkdir()
    except FileExistsError as exc:
        raise PathNotAllowed(T.PROJECT_EXISTS) from exc
    main_file = root / "main.py"
    try:
        main_file.write_text(PYTHON_MAIN_TEMPLATE, encoding="utf-8", newline="\n")
    except OSError:
        # Only the file created above: the folder did not exist before this call.
        main_file.unlink(missing_ok=True)
        root.rmdir()
        raise
    return Project.open(root)
