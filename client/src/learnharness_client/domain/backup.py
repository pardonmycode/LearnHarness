"""Rotating pre-save backups outside the Godot project."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


class BackupManager:
    def __init__(self, base_dir: Path, project_id: str, keep: int = 20) -> None:
        self.base_dir = base_dir / "backups" / project_id
        self.keep = keep

    def create(self, relative_path: Path, data: bytes) -> Path:
        target_dir = self.base_dir / relative_path.parent / relative_path.name
        target_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        target = target_dir / f"{timestamp}.bak"
        target.write_bytes(data)
        backups = sorted(target_dir.glob("*.bak"), reverse=True)
        for old in backups[self.keep :]:
            old.unlink(missing_ok=True)
        return target

    def list_for(self, relative_path: Path) -> list[Path]:
        target_dir = self.base_dir / relative_path.parent / relative_path.name
        return sorted(target_dir.glob("*.bak"), reverse=True) if target_dir.exists() else []
