from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.domain.project import GodotProject
from learnharness_client.ui.editor import editor_tabs as editor_tabs_module
from learnharness_client.ui.editor.editor_tabs import EditorTabs


class StubSettings:
    font_size = 14


def test_generated_file_is_backed_up_and_written_atomically(
    qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    data_dir = tmp_path / "app-data"
    monkeypatch.setattr(editor_tabs_module, "app_data_dir", lambda: data_dir)
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "project.godot").write_text(
        '[application]\nconfig/name="Test"\n', encoding="utf-8"
    )
    script = project_root / "player.gd"
    script.write_bytes(b"extends Node\n")
    tabs = EditorTabs(StubSettings())  # type: ignore[arg-type]
    qtbot.addWidget(tabs)
    tabs.set_project(GodotProject.open(project_root))
    tabs.open_file(script)

    generated = "extends Node2D\n\nfunc _ready():\n\tpass\n"
    assert tabs.apply_generated_file("player.gd", generated)
    assert script.read_text(encoding="utf-8") == generated
    backups = list((data_dir / "backups").rglob("*.bak"))
    assert backups
    assert backups[0].read_bytes() == b"extends Node\n"
