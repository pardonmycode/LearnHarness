"""Godot project discovery and metadata."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from ..texts import T
from .path_guard import PathGuard, PathNotAllowed, fold_case

_PROJECT_NAME = re.compile(r'^config/name\s*=\s*"((?:[^"\\]|\\.)*)"\s*$', re.MULTILINE)


@dataclass(frozen=True, slots=True)
class GodotProject:
    root: Path
    name: str
    project_id: str
    guard: PathGuard

    @classmethod
    def open(cls, root: Path | str) -> GodotProject:
        candidate = Path(root).resolve(strict=True)
        descriptor = candidate / "project.godot"
        if not descriptor.is_file():
            raise PathNotAllowed(T.PROJECT_MISSING_DESCRIPTOR)
        text = descriptor.read_text(encoding="utf-8-sig", errors="replace")
        match = _PROJECT_NAME.search(text)
        name = match.group(1).replace(r"\"", '"') if match else candidate.name
        # Same id on Windows as before; on Linux "Spiel" and "spiel" are different projects.
        digest = hashlib.sha256(fold_case(str(candidate)).encode("utf-8")).hexdigest()[:16]
        return cls(candidate, name, digest, PathGuard(candidate))
