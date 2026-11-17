"""Crash-recovery drafts stored outside the Godot project."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .script_document import ScriptDocument


@dataclass(frozen=True, slots=True)
class RecoveryDraft:
    project_id: str
    relative_path: Path
    content_path: Path
    saved_at: str


class RecoveryManager:
    def __init__(self, base_dir: Path) -> None:
        self.root = base_dir / "recovery"

    def _paths(self, project_id: str, relative_path: Path) -> tuple[Path, Path]:
        safe_name = "__".join(relative_path.parts)
        directory = self.root / project_id
        return directory / f"{safe_name}.draft", directory / f"{safe_name}.json"

    def write(self, project_id: str, relative_path: Path, document: ScriptDocument) -> None:
        content_path, metadata_path = self._paths(project_id, relative_path)
        content_path.parent.mkdir(parents=True, exist_ok=True)
        content_path.write_text(document.text, encoding="utf-8", newline="")
        metadata_path.write_text(
            json.dumps(
                {
                    "project_id": project_id,
                    "relative_path": relative_path.as_posix(),
                    "saved_at": datetime.now(UTC).isoformat(),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def clear(self, project_id: str, relative_path: Path) -> None:
        for path in self._paths(project_id, relative_path):
            path.unlink(missing_ok=True)

    def list_for_project(self, project_id: str) -> list[RecoveryDraft]:
        directory = self.root / project_id
        if not directory.exists():
            return []
        drafts: list[RecoveryDraft] = []
        for metadata_path in directory.glob("*.json"):
            try:
                data = json.loads(metadata_path.read_text(encoding="utf-8"))
                relative = Path(str(data["relative_path"]))
                content_path, _ = self._paths(project_id, relative)
                if content_path.is_file():
                    drafts.append(
                        RecoveryDraft(project_id, relative, content_path, str(data["saved_at"]))
                    )
            except (OSError, KeyError, ValueError, TypeError, json.JSONDecodeError):
                continue
        return sorted(drafts, key=lambda item: item.saved_at, reverse=True)
