"""Centralized project-bound path validation."""

from __future__ import annotations

import os
import stat
from pathlib import Path


class PathNotAllowed(ValueError):
    """Raised when a path would escape the selected Godot project."""


class PathGuard:
    EXCLUDED_DIRECTORIES = frozenset({".godot", ".import", ".git"})

    def __init__(
        self,
        project_root: Path,
        *,
        allowed_suffixes: frozenset[str] = frozenset({".gd"}),
        include_addons: bool = False,
    ) -> None:
        self.root = project_root.resolve(strict=True)
        if not (self.root / "project.godot").is_file():
            raise PathNotAllowed("Der gewählte Ordner ist kein Godot-Projekt.")
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
            raise PathNotAllowed("Verknüpfte Ordner und Dateien sind hier nicht erlaubt.")

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
        if folded & self.EXCLUDED_DIRECTORIES:
            raise PathNotAllowed("Dieser Projektordner ist geschützt.")
        if not self.include_addons and "addons" in folded:
            raise PathNotAllowed("Add-ons sind standardmäßig ausgeblendet.")

        current = self.root
        for part in parent_parts:
            current /= part
            if (current / ".gdignore").exists():
                raise PathNotAllowed("Dieser Ordner wird von Godot ignoriert.")

    def ensure_allowed(self, path: Path | str, *, must_exist: bool = True) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        absolute = candidate.absolute()
        if not absolute.is_relative_to(self.root) or absolute == self.root:
            raise PathNotAllowed("Die Datei liegt außerhalb des Godot-Projekts.")
        # Inspect the un-resolved path first. Resolving would otherwise hide a
        # symlink or Windows junction that points back into the project.
        self._check_components(absolute)
        try:
            resolved = absolute.resolve(strict=must_exist)
        except FileNotFoundError as exc:
            raise PathNotAllowed("Die Skriptdatei wurde nicht gefunden.") from exc
        if not resolved.is_relative_to(self.root) or resolved == self.root:
            raise PathNotAllowed("Die Datei liegt außerhalb des Godot-Projekts.")
        if resolved.suffix.casefold() not in self.allowed_suffixes:
            raise PathNotAllowed("Es dürfen nur GDScript-Dateien geöffnet werden.")
        self._check_components(resolved)
        self._check_exclusions(resolved)
        if must_exist and not resolved.is_file():
            raise PathNotAllowed("Der Pfad ist keine Skriptdatei.")
        return resolved

    def relative(self, path: Path | str) -> Path:
        return self.ensure_allowed(path).relative_to(self.root)

    def iter_scripts(self) -> list[Path]:
        scripts: list[Path] = []
        for candidate in self.root.rglob("*.gd"):
            try:
                scripts.append(self.ensure_allowed(candidate))
            except PathNotAllowed:
                continue
        return sorted(scripts, key=lambda item: str(item.relative_to(self.root)).casefold())
