"""Godot folders and path comparisons on Windows, Linux and macOS."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from learnharness_client.domain import path_guard
from learnharness_client.godot import paths
from learnharness_client.godot.log_reader import default_log_path
from learnharness_client.ui import main_window


def test_windows_uses_appdata_for_everything() -> None:
    env = {"APPDATA": r"C:\Users\kind\AppData\Roaming"}
    expected = Path(r"C:\Users\kind\AppData\Roaming") / "Godot"
    assert paths.godot_config_dir(env, "win32") == expected
    assert paths.godot_data_dir(env, "win32") == expected
    assert paths.godot_config_dir({}, "win32") is None


def test_linux_follows_xdg_with_home_fallback() -> None:
    env = {"HOME": "/home/kind"}
    assert paths.godot_config_dir(env, "linux") == Path("/home/kind/.config/godot")
    assert paths.godot_data_dir(env, "linux") == Path("/home/kind/.local/share/godot")
    xdg = {**env, "XDG_CONFIG_HOME": "/cfg", "XDG_DATA_HOME": "/data"}
    assert paths.godot_config_dir(xdg, "linux") == Path("/cfg/godot")
    assert paths.godot_data_dir(xdg, "linux") == Path("/data/godot")
    # Relative XDG values are invalid by the spec and ignored.
    assert paths.godot_config_dir({**env, "XDG_CONFIG_HOME": "rel"}, "linux") == Path(
        "/home/kind/.config/godot"
    )


def test_macos_uses_application_support() -> None:
    env = {"HOME": "/Users/kind"}
    expected = Path("/Users/kind/Library/Application Support/Godot")
    assert paths.godot_config_dir(env, "darwin") == expected
    assert paths.godot_data_dir(env, "darwin") == expected


def test_log_path_on_linux_layout() -> None:
    data = paths.godot_data_dir({"HOME": "/home/kind"}, "linux")
    assert default_log_path("Mein Spiel", data) == Path(
        "/home/kind/.local/share/godot/app_userdata/Mein Spiel/logs/godot.log"
    )


@pytest.mark.parametrize("insensitive", [True, False])
def test_target_file_respects_case_rules(
    monkeypatch: pytest.MonkeyPatch, insensitive: bool
) -> None:
    monkeypatch.setattr(path_guard, "CASE_INSENSITIVE_FS", insensitive)
    assert main_window.is_target_file("scripts\\player.gd", "scripts/player.gd")
    assert main_window.is_target_file("./Scripts/Player.gd", "scripts/player.gd") is insensitive


def test_godot_from_path(monkeypatch: pytest.MonkeyPatch) -> None:
    found = {"godot4": "/usr/bin/godot4"}
    monkeypatch.setattr(paths.shutil, "which", lambda name: found.get(name))
    assert paths.find_godot_on_path() == "/usr/bin/godot4"
    found.clear()
    assert paths.find_godot_on_path() == ""


def test_backslash_is_a_separator_on_every_system(tmp_path: Path) -> None:
    (tmp_path / "project.godot").write_text('config/name="T"\n', encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "player.gd").write_text("extends Node\n", encoding="utf-8")
    guard = path_guard.PathGuard(tmp_path)
    assert guard.ensure_allowed(r"scripts\player.gd") == (tmp_path / "scripts/player.gd").resolve()
    with pytest.raises(path_guard.PathNotAllowed):
        guard.ensure_allowed(r"..\outside.gd", must_exist=False)


@pytest.mark.skipif(sys.platform == "win32", reason=r"Windows does not allow \ in file names")
def test_linux_file_named_with_backslash_is_refused(tmp_path: Path) -> None:
    (tmp_path / "project.godot").write_text('config/name="T"\n', encoding="utf-8")
    odd = tmp_path / r"..\trick.gd"
    odd.write_text("extends Node\n", encoding="utf-8")
    guard = path_guard.PathGuard(tmp_path)
    with pytest.raises(path_guard.PathNotAllowed):
        guard.ensure_allowed(odd)
    assert odd not in guard.iter_scripts()
