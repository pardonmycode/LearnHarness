"""The terminal starts the project, shows output, takes input and can be stopped."""

from __future__ import annotations

from pathlib import Path

import pytest
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QSplitter
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.config import AppSettings
from learnharness_client.domain import run_target as run_target_module
from learnharness_client.domain.profile import StudentProfile
from learnharness_client.domain.project import Project, create_python_project
from learnharness_client.domain.run_target import RunNotPossible, run_target, script_to_run
from learnharness_client.net.fake_tutor_client import FakeTutorClient
from learnharness_client.texts import T
from learnharness_client.ui.editor import editor_tabs as editor_tabs_module
from learnharness_client.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch) -> MainWindow:
    monkeypatch.setattr(editor_tabs_module, "app_data_dir", lambda: tmp_path / "data")
    settings = AppSettings()
    settings._settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    profile = StudentProfile.create("Fuchs", 1)
    settings.save_student_profile(profile)
    main = MainWindow(settings, FakeTutorClient(delay_ms=1), profile, server_url="fake")
    qtbot.addWidget(main)
    main.open_project(create_python_project(tmp_path, "Spiel"))
    yield main
    main.terminal.shutdown()


def _run(qtbot: QtBot, window: MainWindow, code: str) -> str:
    window.editor_tabs.current_editor().setPlainText(code)
    with qtbot.waitSignal(window.terminal.process.finished, timeout=10_000):
        window.run_script()
    qtbot.waitUntil(lambda: not window.terminal.is_running())
    return window.terminal.output.toPlainText()


def test_terminal_sits_below_tree_and_code(window: MainWindow) -> None:
    left = window.splitter.widget(0)
    assert isinstance(left, QSplitter)
    assert left.widget(1) is window.terminal
    assert window.splitter.widget(1) is window.learning_tabs
    assert window.script_tree.parent() is left.widget(0)
    assert window.editor_tabs.parent() is left.widget(0)


def test_run_saves_first_and_shows_umlauts(qtbot: QtBot, window: MainWindow) -> None:
    output = _run(qtbot, window, 'print("Größe: 3")\n')
    assert "Größe: 3" in output and T.TERMINAL_FINISHED in output
    assert not window.editor_tabs.current_document().dirty
    assert "Größe" in (window.project.root / "main.py").read_text(encoding="utf-8")


def test_error_is_shown(qtbot: QtBot, window: MainWindow) -> None:
    output = _run(qtbot, window, 'raise ValueError("kaputt")\n')
    assert "ValueError: kaputt" in output
    assert T.TERMINAL_FAILED.format(code=1) in output


def test_input_reaches_the_program(qtbot: QtBot, window: MainWindow) -> None:
    window.editor_tabs.current_editor().setPlainText('n = input("Name? ")\nprint("Hallo", n)\n')
    window.run_script()
    terminal = window.terminal
    qtbot.waitUntil(lambda: "Name?" in terminal.output.toPlainText(), timeout=10_000)
    assert terminal.input.isEnabled()
    terminal.input.setText("Fuchs")
    with qtbot.waitSignal(terminal.process.finished, timeout=10_000):
        terminal.input.returnPressed.emit()
    qtbot.waitUntil(lambda: "Hallo Fuchs" in terminal.output.toPlainText())


def test_endless_output_can_be_stopped(qtbot: QtBot, window: MainWindow) -> None:
    window.editor_tabs.current_editor().setPlainText('while True:\n    print("x" * 200)\n')
    window.run_script()
    terminal = window.terminal
    qtbot.waitUntil(lambda: "xxx" in terminal.output.toPlainText(), timeout=10_000)
    assert terminal.stop_button.isEnabled() and not terminal.start_button.isEnabled()
    with qtbot.waitSignal(terminal.process.finished, timeout=5_000):
        terminal.stop_button.click()
    qtbot.waitUntil(lambda: T.TERMINAL_STOPPED in terminal.output.toPlainText())
    assert terminal.output.document().blockCount() <= 2000
    assert terminal.start_button.isEnabled()


def test_building_block_starts_the_game_with_working_imports(
    qtbot: QtBot, window: MainWindow
) -> None:
    root = window.project.root
    (root / "game").mkdir()
    (root / "game" / "__init__.py").write_text("", encoding="utf-8")
    (root / "game" / "player.py").write_text('NAME = "Fuchs"\n', encoding="utf-8")
    (root / "main.py").write_text(
        'from game.player import NAME\nprint("Spieler", NAME)\n', encoding="utf-8"
    )
    window.editor_tabs.check_all_external_changes()
    window.editor_tabs.open_file(root / "game" / "player.py")
    assert "main.py" in window.terminal.start_button.text()
    with qtbot.waitSignal(window.terminal.process.finished, timeout=10_000):
        window.run_script()
    qtbot.waitUntil(lambda: T.TERMINAL_FINISHED in window.terminal.output.toPlainText())
    assert "Spieler Fuchs" in window.terminal.output.toPlainText()


def test_switching_project_ends_the_program(
    qtbot: QtBot, window: MainWindow, tmp_path: Path
) -> None:
    window.editor_tabs.current_editor().setPlainText("import time\ntime.sleep(30)\n")
    window.run_script()
    qtbot.waitUntil(window.terminal.is_running)
    window.open_project(create_python_project(tmp_path, "Anderes"))
    assert not window.terminal.is_running()


def test_script_choice_and_missing_tools(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    project = create_python_project(tmp_path, "Wahl")
    helper = project.root / "helfer.py"
    helper.write_text("x = 1\n", encoding="utf-8")
    assert script_to_run(project, helper) == helper
    assert script_to_run(project, None) == project.root / "main.py"
    monkeypatch.setattr(run_target_module, "find_python", lambda: None)
    with pytest.raises(RunNotPossible):
        run_target(project, helper)
    godot_root = tmp_path / "godot"
    godot_root.mkdir()
    (godot_root / "project.godot").write_text('config/name="G"\n', encoding="utf-8")
    with pytest.raises(RunNotPossible):
        run_target(Project.open(godot_root), None, "")
    target = run_target(Project.open(godot_root), None, "/bin/godot")
    assert target.arguments == ("--path", str(godot_root.resolve()))
