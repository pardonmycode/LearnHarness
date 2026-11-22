"""Centralized project-bound path validation."""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path
from typing import Literal

from ..texts import T

ProjectLanguage = Literal["gdscript", "python"]

# Windows and (by default) macOS ignore upper/lower case in file names; Linux does not.
CASE_INSENSITIVE_FS = sys.platform in ("win32", "darwin")


def fold_case(text: str) -> str:
    """Normalise a path text for comparisons the way the file system compares names:
    on Linux ``Player.gd`` and ``player.gd`` are two different files."""
    return text.casefold() if CASE_INSENSITIVE_FS else text


class PathNotAllowed(ValueError):
    """Raised when a path would escape the selected project."""


class PathGuard:
    EXCLUDED_DIRECTORIES = frozenset({".godot", ".import", ".git"})
    # Installed or generated code; hidden folders and virtual environments count as well.
    PYTHON_EXCLUDED_DIRECTORIES = frozenset({"__pycache__", "node_modules", "site-packages"})
    MAX_SCRIPTS = 2000

    def __init__(
        self,
        project_root: Path,
        *,
        allowed_suffixes: frozenset[str] | None = None,
        include_addons: bool = False,
        language: ProjectLanguage = "gdscript",
    ) -> None:
        self.root = project_root.resolve(strict=True)
        self.language: ProjectLanguage = language
        if language == "gdscript" and not (self.root / "project.godot").is_file():
            raise PathNotAllowed(T.PATH_NOT_PROJECT)
        if allowed_suffixes is None:
            allowed_suffixes = frozenset({".py" if language == "python" else ".gd"})
        self.allowed_suffixes = frozenset(suffix.casefold() for suffix in allowed_suffixes)
        self.include_addons = include_addons
        self._reject_reparse_point(self.root)

    def _reject_reparse_point(self, path: Path) -> None:
        try:
            info = os.lstat(path)
        except FileNotFoundError:
            return
        attributes = getattr(info, "st_file_attributes", 0)
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        if stat.S_ISLNK(info.st_mode) or attributes & reparse_flag:
            raise PathNotAllowed(T.PATH_LINKED)

    def _check_components(self, resolved: Path) -> None:
        relative = resolved.relative_to(self.root)
        current = self.root
        for part in relative.parts:
            current /= part
            self._reject_reparse_point(current)

    def _check_exclusions(self, resolved: Path) -> None:
        relative = resolved.relative_to(self.root)
        parent_parts = relative.parts[:-1] if resolved.suffix else relative.parts
        folded = {part.casefold() for part in parent_parts}
        if self.language == "python":
            current = self.root
            for part in parent_parts:
                current /= part
                if self.skips_folder(current):
                    raise PathNotAllowed(T.PATH_PROTECTED)
            return
        if folded & self.EXCLUDED_DIRECTORIES:
            raise PathNotAllowed(T.PATH_PROTECTED)
        if not self.include_addons and "addons" in folded:
            raise PathNotAllowed(T.PATH_ADDONS)

        current = self.root
        for part in parent_parts:
            current /= part
            if (current / ".gdignore").exists():
                raise PathNotAllowed(T.PATH_GDIGNORE)

    def skips_folder(self, folder: Path) -> bool:
        """True for folders that never contain the child's own scripts."""
        name = folder.name.casefold()
        if self.language == "python":
            return (
                name.startswith(".")
                or name in self.PYTHON_EXCLUDED_DIRECTORIES
                or (folder / "pyvenv.cfg").exists()
            )
        return (
            name in self.EXCLUDED_DIRECTORIES
            or (name == "addons" and not self.include_addons)
            or (folder / ".gdignore").exists()
        )

    def ensure_allowed(self, path: Path | str, *, must_exist: bool = True) -> Path:
        if isinstance(path, str):
            # Paths from the server or a Windows PC may use "\". On Linux "\" is an ordinary
            # character, so "..\x.gd" would slip through as a harmless file name.
            path = path.replace("\\", "/")
        candidate = Path(path)
        if os.sep != "\\" and any("\\" in part for part in candidate.parts):
            raise PathNotAllowed(T.PATH_OUTSIDE)  # e.g. a Linux file literally named "..\x.gd"
        if not candidate.is_absolute():
            candidate = self.root / candidate
        absolute = candidate.absolute()
        if not absolute.is_relative_to(self.root) or absolute == self.root:
            raise PathNotAllowed(T.PATH_OUTSIDE)
        # Inspect the un-resolved path first. Resolving would otherwise hide a
        # symlink or Windows junction that points back into the project.
        self._check_components(absolute)
        try:
            resolved = absolute.resolve(strict=must_exist)
        except FileNotFoundError as exc:
            raise PathNotAllowed(T.PATH_NOT_FOUND) from exc
        if not resolved.is_relative_to(self.root) or resolved == self.root:
            raise PathNotAllowed(T.PATH_OUTSIDE)
        if resolved.suffix.casefold() not in self.allowed_suffixes:
            raise PathNotAllowed(T.PATH_ONLY_PY if self.language == "python" else T.PATH_ONLY_GD)
        self._check_components(resolved)
        self._check_exclusions(resolved)
        if must_exist and not resolved.is_file():
            raise PathNotAllowed(T.PATH_NOT_FILE)
        return resolved

    def relative(self, path: Path | str) -> Path:
        return self.ensure_allowed(path).relative_to(self.root)

    def iter_scripts(self) -> list[Path]:
        scripts: list[Path] = []
        for folder, subfolders, files in os.walk(self.root):
            current = Path(folder)
            subfolders[:] = [name for name in subfolders if not self.skips_folder(current / name)]
            for name in files:
                if Path(name).suffix.casefold() not in self.allowed_suffixes:
                    continue
                try:
                    scripts.append(self.ensure_allowed(current / name))
                except PathNotAllowed:
                    continue
            if len(scripts) >= self.MAX_SCRIPTS:
                del scripts[self.MAX_SCRIPTS :]
                break
        return sorted(scripts, key=lambda item: str(item.relative_to(self.root)).casefold())
