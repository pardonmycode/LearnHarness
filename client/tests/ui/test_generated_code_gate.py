from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.domain.limits import MAX_FILE_CONTEXT
from learnharness_client.domain.project import GodotProject
from learnharness_client.texts import T
from learnharness_client.ui.editor import editor_tabs as editor_tabs_module
from learnharness_client.ui.editor.editor_tabs import EditorTabs
from learnharness_client.ui.editor.editor_tabs import files as files_module


class StubSettings:
    font_size = 14
    autosave = False


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


def _tabs_with_script(
    qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch, text: str
) -> tuple[EditorTabs, Path, list[str]]:
    monkeypatch.setattr(editor_tabs_module, "app_data_dir", lambda: tmp_path / "app-data")
    warnings: list[str] = []
    monkeypatch.setattr(
        files_module.QMessageBox, "warning", lambda _parent, title, _text: warnings.append(title)
    )
    root = tmp_path / "project"
    root.mkdir()
    (root / "project.godot").write_text('[application]\nconfig/name="T"\n', encoding="utf-8")
    script = root / "player.gd"
    script.write_text(text, encoding="utf-8")
    tabs = EditorTabs(StubSettings())  # type: ignore[arg-type]
    qtbot.addWidget(tabs)
    tabs.set_project(GodotProject.open(root))
    tabs.open_file(script)
    return tabs, script, warnings


def test_too_long_script_is_never_replaced(
    qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    long_text = "x" * (MAX_FILE_CONTEXT + 1)
    tabs, script, warnings = _tabs_with_script(qtbot, tmp_path, monkeypatch, long_text)
    assert not tabs.apply_generated_file("player.gd", "kurz\n")
    assert script.read_text(encoding="utf-8") == long_text
    assert tabs.current_editor().toPlainText() == long_text
    assert warnings == [T.FILE_TOO_LONG_TITLE]


def test_script_at_the_limit_can_still_be_written(
    qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    text = "x" * MAX_FILE_CONTEXT
    tabs, script, warnings = _tabs_with_script(qtbot, tmp_path, monkeypatch, text)
    assert tabs.apply_generated_file("player.gd", text + "\nneu\n")
    assert script.read_text(encoding="utf-8").endswith("neu\n") and not warnings


def test_script_changed_since_the_request_stays(
    qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    tabs, script, warnings = _tabs_with_script(qtbot, tmp_path, monkeypatch, "alt\n")
    editor = tabs.current_editor()
    editor.setPlainText("mein neuer Code\n")
    assert tabs.save_editor(editor)
    assert not tabs.apply_generated_file("player.gd", "von der KI\n", "alt\n")
    assert script.read_text(encoding="utf-8") == "mein neuer Code\n"
    assert warnings == [T.FILE_CHANGED_TITLE]
    assert tabs.apply_generated_file("player.gd", "von der KI\n", "mein neuer Code\n")
    assert script.read_text(encoding="utf-8") == "von der KI\n"
