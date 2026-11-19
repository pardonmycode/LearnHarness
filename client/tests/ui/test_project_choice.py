"""Finding Godot's known projects and choosing one at first start."""

from __future__ import annotations

from pathlib import Path

from pytestqt.qtbot import QtBot

from learnharness_client.godot.project_list import known_godot_projects, parse_project_paths
from learnharness_client.ui import project_picker
from learnharness_client.ui.dialogs.project_choice_dialog import ProjectChoiceDialog


def _project(root: Path, name: str) -> Path:
    folder = root / name
    folder.mkdir(parents=True)
    (folder / "project.godot").write_text(f'config/name="{name}"\n', encoding="utf-8")
    return folder


def _write_cfg(appdata: Path, text: str, filename: str = "projects.cfg") -> None:
    (appdata / "Godot").mkdir(parents=True, exist_ok=True)
    (appdata / "Godot" / filename).write_text(text, encoding="utf-8")


def test_known_projects_are_parsed_filtered_and_deduplicated(tmp_path: Path) -> None:
    first = _project(tmp_path, "Jump")
    second = _project(tmp_path, "Space Race")
    missing = tmp_path / "Weg"
    upper = str(first).upper().replace("\\", "/")
    _write_cfg(
        tmp_path / "appdata",
        f'["{first.as_posix()}"]\n\nfavorite=false\n\n'
        f'["{missing.as_posix()}"]\n\nfavorite=true\n\n'
        f'["{second.as_posix()}"]\n\nfavorite=false\n\n'
        f'["{upper}"]\n\nfavorite=false\n',
    )
    found = known_godot_projects(tmp_path / "appdata" / "Godot")
    assert [path.name for path in found] == ["Jump", "Space Race"]


def test_godot3_entries_and_escaped_paths(tmp_path: Path) -> None:
    old = _project(tmp_path, "Old")
    _write_cfg(
        tmp_path / "appdata",
        f'[resource]\nprojects/old = "{old.as_posix()}"\n',
        "editor_settings-3.tres",
    )
    assert known_godot_projects(tmp_path / "appdata" / "Godot") == [old]
    assert parse_project_paths('["C:/a \\"b\\""]\n') == ['C:/a "b"']


def test_broken_or_missing_files_give_empty_list(tmp_path: Path) -> None:
    assert known_godot_projects(tmp_path / "Godot") == []
    (tmp_path / "Godot").mkdir()
    (tmp_path / "Godot" / "projects.cfg").write_bytes(b"\xff\xfe[[[\x00garbage")
    assert known_godot_projects(tmp_path / "Godot") == []


def test_dialog_lists_recent_first_and_returns_selection(qtbot: QtBot, tmp_path: Path) -> None:
    recent = _project(tmp_path, "Recent")
    known = _project(tmp_path, "Known")
    dialog = ProjectChoiceDialog([known, recent, tmp_path / "missing"], [str(recent)])
    qtbot.addWidget(dialog)
    assert dialog.project_count() == 2
    assert dialog.projects.item(0).text().startswith("Recent")
    dialog.projects.setCurrentRow(1)
    dialog.open_button.click()
    assert dialog.selected is not None
    assert dialog.selected.name == "Known"


def test_picker_falls_back_to_folder_dialog_without_projects(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        project_picker, "choose_project_folder", lambda _parent, start: calls.append(start)
    )
    assert project_picker.choose_project(None, "C:/start", known=[]) is None
    assert calls == ["C:/start"]
