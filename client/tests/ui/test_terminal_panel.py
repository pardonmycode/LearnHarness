"""Children type commands into the terminal; there are no buttons."""

from __future__ import annotations

from pathlib import Path

import pytest
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import QPushButton, QSplitter
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import StudentProfile
from learnharness_client.domain.project import create_python_project
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


def _type(qtbot: QtBot, window: MainWindow, line: str) -> None:
    qtbot.keyClicks(window.terminal.console, line)
    qtbot.keyClick(window.terminal.console, Qt.Key.Key_Return)


def _text(window: MainWindow) -> str:
    return window.terminal.console.toPlainText()


def _run(qtbot: QtBot, window: MainWindow, line: str) -> str:
    with qtbot.waitSignal(window.terminal.process.finished, timeout=10_000):
        _type(qtbot, window, line)
    qtbot.waitUntil(lambda: _text(window).endswith("$ "))
    return _text(window)


def test_terminal_sits_below_code_and_has_no_buttons(window: MainWindow) -> None:
    left = window.splitter.widget(0)
    assert isinstance(left, QSplitter)
    assert left.widget(1) is window.terminal
    assert window.splitter.widget(1) is window.learning_area
    assert window.terminal.findChildren(QPushButton) == []


def test_typing_python_main_saves_and_runs(qtbot: QtBot, window: MainWindow) -> None:
    window.editor_tabs.current_editor().setPlainText('print("Größe: 3")\n')
    output = _run(qtbot, window, "python main.py")
    assert "Spiel $ python main.py\nGröße: 3\nSpiel $ " in output
    assert not window.editor_tabs.current_document().dirty


def test_error_is_shown(qtbot: QtBot, window: MainWindow) -> None:
    window.editor_tabs.current_editor().setPlainText('raise ValueError("kaputt")\n')
    assert "ValueError: kaputt" in _run(qtbot, window, "python main.py")


def test_input_reaches_the_program(qtbot: QtBot, window: MainWindow) -> None:
    window.editor_tabs.current_editor().setPlainText('n = input("Name? ")\nprint("Hallo", n)\n')
    _type(qtbot, window, "python main.py")
    qtbot.waitUntil(lambda: "Name?" in _text(window), timeout=10_000)
    with qtbot.waitSignal(window.terminal.process.finished, timeout=10_000):
        _type(qtbot, window, "Fuchs")
    qtbot.waitUntil(lambda: "Name? Fuchs\nHallo Fuchs" in _text(window))


def test_ctrl_c_stops_endless_output(qtbot: QtBot, window: MainWindow) -> None:
    window.editor_tabs.current_editor().setPlainText('while True:\n    print("x" * 200)\n')
    _type(qtbot, window, "python main.py")
    qtbot.waitUntil(lambda: "xxx" in _text(window), timeout=10_000)
    with qtbot.waitSignal(window.terminal.process.finished, timeout=5_000):
        qtbot.keyClick(window.terminal.console, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
    qtbot.waitUntil(lambda: T.TERMINAL_STOPPED in _text(window))
    assert window.terminal.console.document().blockCount() <= 2000


def test_system_commands_do_not_run(qtbot: QtBot, window: MainWindow, tmp_path: Path) -> None:
    marker = tmp_path / "ran"
    for line in (f"touch {marker}", f"python -c open('{marker}','w')", f"ls; touch {marker}"):
        _type(qtbot, window, line)
    assert not marker.exists()
    assert not window.terminal.is_running()
    assert "kenne ich nicht" in _text(window)


def test_cd_ls_and_imports(qtbot: QtBot, window: MainWindow) -> None:
    root = window.project.root
    (root / "game").mkdir()
    (root / ".venv").mkdir()
    (root / "game" / "__init__.py").write_text("", encoding="utf-8")
    (root / "game" / "player.py").write_text('NAME = "Fuchs"\n', encoding="utf-8")
    (root / "game" / "start.py").write_text(
        'from game.player import NAME\nprint("Spieler", NAME)\n', encoding="utf-8"
    )
    _type(qtbot, window, "ls")
    assert "game/\nmain.py" in _text(window) and ".venv" not in _text(window)
    _type(qtbot, window, "cd game")
    assert _text(window).endswith("Spiel/game $ ")
    assert "Spieler Fuchs" in _run(qtbot, window, "python start.py")
    _type(qtbot, window, "cd ../..")
    assert T.PATH_OUTSIDE in _text(window)
    _type(qtbot, window, "cd ..")
    assert _text(window).endswith("Spiel $ ")


def test_old_output_cannot_be_edited(qtbot: QtBot, window: MainWindow) -> None:
    console = window.terminal.console
    before = _text(window)
    for _ in range(3):
        qtbot.keyClick(console, Qt.Key.Key_Backspace)
    assert _text(window) == before
    console.selectAll()
    qtbot.keyClicks(console, "ls")
    assert _text(window) == before + "ls"


def test_up_arrow_brings_back_the_last_command(qtbot: QtBot, window: MainWindow) -> None:
    _type(qtbot, window, "pwd")
    qtbot.keyClick(window.terminal.console, Qt.Key.Key_Up)
    assert window.terminal.console.input_text() == "pwd"


def test_switching_project_ends_the_program(
    qtbot: QtBot, window: MainWindow, tmp_path: Path
) -> None:
    window.editor_tabs.current_editor().setPlainText("import time\ntime.sleep(30)\n")
    _type(qtbot, window, "python main.py")
    qtbot.waitUntil(window.terminal.is_running)
    window.open_project(create_python_project(tmp_path, "Anderes"))
    assert not window.terminal.is_running()
    assert _text(window).endswith("Anderes $ ")


def test_tabs_start_wide_and_the_divider_can_be_dragged(qtbot: QtBot, window: MainWindow) -> None:
    with qtbot.waitExposed(window):
        window.resize(1400, 860)
        window.show()
    qtbot.waitUntil(lambda: window.splitter.width() >= 1300)
    window._restore_window_state()
    left, tabs = window.splitter.sizes()
    assert 0.50 < tabs / (left + tabs) < 0.56
    window.splitter.moveSplitter(left + 250, 1)
    assert window.splitter.sizes()[0] == left + 250
    window.splitter.moveSplitter(0, 1)
    assert window.work_splitter.minimumWidth() <= window.splitter.sizes()[0] < left
    moved = window.splitter.sizes()
    window.settings.set_value("window/main_splitter_v2", moved)
    window._restore_window_state()
    assert window.splitter.sizes() == moved
