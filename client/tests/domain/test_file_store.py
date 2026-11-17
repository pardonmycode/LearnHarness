from __future__ import annotations

from pathlib import Path

import pytest

from learnharness_client.domain.backup import BackupManager
from learnharness_client.domain.file_store import FileStore, SaveConflict
from learnharness_client.domain.path_guard import PathGuard


def make_store(tmp_path: Path) -> tuple[Path, FileStore]:
    project = tmp_path / "project"
    project.mkdir()
    (project / "project.godot").write_text('[application]\nconfig/name="Test"\n')
    store = FileStore(PathGuard(project), BackupManager(tmp_path / "data", "project"))
    return project, store


@pytest.mark.parametrize(
    "data",
    [
        b"extends Node\n\tvar speed = 10\n",
        b"\xef\xbb\xbfextends Node\r\n# Gr\xc3\xbc\xc3\x9fe\r\n",
        b"extends Node",
    ],
)
def test_roundtrip_preserves_bytes(tmp_path: Path, data: bytes) -> None:
    project, store = make_store(tmp_path)
    script = project / "player.gd"
    script.write_bytes(data)
    document = store.load(script)
    document.dirty = True
    store.save(document)
    assert script.read_bytes() == data


def test_external_change_raises_conflict(tmp_path: Path) -> None:
    project, store = make_store(tmp_path)
    script = project / "player.gd"
    script.write_text("extends Node\n", encoding="utf-8")
    document = store.load(script)
    document.update_text("extends Node2D\n")
    script.write_text("extends CharacterBody2D\n", encoding="utf-8")
    with pytest.raises(SaveConflict):
        store.save(document)
    assert document.dirty
    assert script.read_text(encoding="utf-8") == "extends CharacterBody2D\n"


def test_save_creates_backup(tmp_path: Path) -> None:
    project, store = make_store(tmp_path)
    script = project / "player.gd"
    script.write_bytes(b"old\n")
    document = store.load(script)
    document.update_text("new\n")
    store.save(document)
    backups = store.backup_manager.list_for(Path("player.gd"))
    assert backups
    assert backups[0].read_bytes() == b"old\n"
