"""The tutor knows the latest error from the terminal and forgets it once it is fixed."""

from __future__ import annotations

from pathlib import Path

import pytest
from project_tab_helpers import _record, make_window
from PyQt6.QtCore import Qt
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.domain.project import create_python_project
from learnharness_client.ui.main_window import MainWindow
from learnharness_client.ui.panels.problems_panel import Problem


@pytest.fixture
def window(qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch):
    main = make_window(qtbot, tmp_path, monkeypatch)
    yield main
    main.terminal.shutdown()


def _run(qtbot: QtBot, window: MainWindow, code: str) -> None:
    editor = window.editor_tabs.current_editor()
    editor.setPlainText(code)
    console = window.terminal.console
    with qtbot.waitSignal(window.terminal.process.finished, timeout=10_000):
        qtbot.keyClicks(console, "python main.py")
        qtbot.keyClick(console, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: console.toPlainText().endswith("$ "))


def test_terminal_error_reaches_the_tutor_without_paths(
    qtbot: QtBot, window: MainWindow, tmp_path: Path
) -> None:
    sent = _record(window)
    _run(qtbot, window, 'print("Hallo")\nprint(punkte)\n')
    with qtbot.waitSignal(window.tutor_client.stream_finished, timeout=3000):
        window.send_tutor_message("Warum kommt ein Fehler?")
    assert "NameError" in sent[0].last_error and "Hallo" not in sent[0].last_error
    assert str(tmp_path) not in sent[0].last_error and "./main.py" in sent[0].last_error


def test_successful_run_forgets_old_errors(qtbot: QtBot, window: MainWindow) -> None:
    window.problems_panel.add_problem(Problem("main.py", 1, "Alter Fehler", "Python"))
    assert window._latest_error() == "Alter Fehler"
    _run(qtbot, window, "print(punkte)\n")
    assert "NameError" in window._latest_error()
    _run(qtbot, window, 'print("ok")\n')
    assert window._latest_error() is None


def test_new_problem_after_a_good_run_counts(qtbot: QtBot, window: MainWindow) -> None:
    window.problems_panel.add_problem(Problem("main.py", 1, "Alter Fehler", "Python"))
    _run(qtbot, window, 'print("ok")\n')
    window.problems_panel.add_problem(Problem("main.py", 2, "Neuer Fehler", "Python"))
    assert window._latest_error() == "Neuer Fehler"


def test_other_project_starts_without_an_error(
    qtbot: QtBot, window: MainWindow, tmp_path: Path
) -> None:
    _run(qtbot, window, "print(punkte)\n")
    window.editor_tabs.save_editor(window.editor_tabs.current_editor())
    window.open_project(create_python_project(tmp_path, "Anderes"))
    assert window.terminal.last_error is None
