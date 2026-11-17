"""In-memory representation of a GDScript file."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

UTF8_BOM = b"\xef\xbb\xbf"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(slots=True)
class ScriptDocument:
    path: Path
    text: str
    disk_hash: str | None
    disk_mtime_ns: int | None
    newline: str = "\n"
    has_bom: bool = False
    dirty: bool = False
    deleted_externally: bool = False

    @classmethod
    def from_bytes(cls, path: Path, data: bytes, mtime_ns: int) -> ScriptDocument:
        has_bom = data.startswith(UTF8_BOM)
        decoded = data[len(UTF8_BOM) :].decode("utf-8") if has_bom else data.decode("utf-8")
        newline = "\r\n" if "\r\n" in decoded else "\n"
        normalized = decoded.replace("\r\n", "\n").replace("\r", "\n")
        return cls(
            path=path,
            text=normalized,
            disk_hash=sha256_bytes(data),
            disk_mtime_ns=mtime_ns,
            newline=newline,
            has_bom=has_bom,
        )

    def to_bytes(self) -> bytes:
        text = self.text.replace("\r\n", "\n").replace("\r", "\n")
        encoded = text.replace("\n", self.newline).encode("utf-8")
        return (UTF8_BOM + encoded) if self.has_bom else encoded

    def update_text(self, text: str) -> None:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        if normalized != self.text:
            self.text = normalized
            self.dirty = True

    def mark_saved(self, data: bytes, mtime_ns: int) -> None:
        self.disk_hash = sha256_bytes(data)
        self.disk_mtime_ns = mtime_ns
        self.dirty = False
        self.deleted_externally = False
