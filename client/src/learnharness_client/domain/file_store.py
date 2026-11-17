"""Load and atomically save guarded GDScript documents."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QIODeviceBase, QSaveFile

from .backup import BackupManager
from .path_guard import PathGuard
from .script_document import ScriptDocument, sha256_bytes


class FileStoreError(OSError):
    pass


class FileTooLarge(FileStoreError):
    pass


class SaveConflict(FileStoreError):
    def __init__(self, message: str, disk_bytes: bytes | None) -> None:
        super().__init__(message)
        self.disk_bytes = disk_bytes


class FileStore:
    def __init__(
        self,
        guard: PathGuard,
        backup_manager: BackupManager,
        *,
        max_bytes: int = 512 * 1024,
    ) -> None:
        self.guard = guard
        self.backup_manager = backup_manager
        self.max_bytes = max_bytes

    def load(self, path: Path | str) -> ScriptDocument:
        allowed = self.guard.ensure_allowed(path)
        stat_result = allowed.stat()
        if stat_result.st_size > self.max_bytes:
            raise FileTooLarge("Diese Datei ist zu groß für den Lerneditor.")
        try:
            data = allowed.read_bytes()
            return ScriptDocument.from_bytes(allowed, data, stat_result.st_mtime_ns)
        except UnicodeDecodeError as exc:
            raise FileStoreError("Die Datei ist nicht als UTF-8 gespeichert.") from exc

    def disk_hash(self, document: ScriptDocument) -> str | None:
        allowed = self.guard.ensure_allowed(document.path, must_exist=False)
        if not allowed.exists():
            return None
        data = allowed.read_bytes()
        return sha256_bytes(data)

    def has_external_change(self, document: ScriptDocument) -> bool:
        return self.disk_hash(document) != document.disk_hash

    def save(self, document: ScriptDocument, *, force: bool = False) -> None:
        allowed = self.guard.ensure_allowed(document.path, must_exist=False)
        disk_bytes = allowed.read_bytes() if allowed.exists() else None
        current_hash = sha256_bytes(disk_bytes) if disk_bytes is not None else None
        if not force and current_hash != document.disk_hash:
            raise SaveConflict(
                "Die Datei wurde seit dem Öffnen in Godot oder einem anderen Programm geändert.",
                disk_bytes,
            )
        if disk_bytes is not None:
            relative = allowed.relative_to(self.guard.root)
            self.backup_manager.create(relative, disk_bytes)

        data = document.to_bytes()
        save_file = QSaveFile(str(allowed))
        if not save_file.open(QIODeviceBase.OpenModeFlag.WriteOnly):
            raise FileStoreError("Die Datei konnte nicht zum Speichern geöffnet werden.")
        if save_file.write(data) != len(data):
            save_file.cancelWriting()
            raise FileStoreError("Die Datei konnte nicht vollständig geschrieben werden.")
        if not save_file.commit():
            raise FileStoreError("Das sichere Speichern konnte nicht abgeschlossen werden.")
        document.path = allowed
        document.mark_saved(data, allowed.stat().st_mtime_ns)

    def create(self, relative_path: Path | str, text: str = "extends Node\n") -> ScriptDocument:
        allowed = self.guard.ensure_allowed(relative_path, must_exist=False)
        if allowed.exists():
            raise FileStoreError("Diese Datei gibt es bereits.")
        allowed.parent.mkdir(parents=True, exist_ok=True)
        document = ScriptDocument(allowed, text, None, None, dirty=True)
        self.save(document)
        return document
