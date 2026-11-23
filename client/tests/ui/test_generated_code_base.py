"""Generated code is only written into the script it was made from."""

from __future__ import annotations

from pathlib import Path

import pytest
from learnharness_protocol import GeneratedFile, ReviewResult, Submission
from project_tab_helpers import make_window
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.texts import T
from learnharness_client.ui.editor.editor_tabs import files as files_module
from learnharness_client.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch) -> MainWindow:
    main = make_window(qtbot, tmp_path, monkeypatch)
    main.settings.show_agent_changes = False
    main.learn_agent_panel.show_changes = False
    main.warnings = []
    monkeypatch.setattr(
        files_module.QMessageBox,
        "warning",
        lambda _parent, title, _text: main.warnings.append(title),
    )
    return main


def _edit_and_save(window: MainWindow, text: str) -> None:
    editor = window.editor_tabs.current_editor()
    editor.setPlainText(text)
    assert window.editor_tabs.save_editor(editor)


def _script(window: MainWindow) -> str:
    return (window.project.root / "main.py").read_text(encoding="utf-8")


def _learn_round(qtbot: QtBot, window: MainWindow) -> None:
    with qtbot.waitSignal(window.tutor_client.stream_finished):
        window.start_learning_round("Begrüßung", 1)


def _answer(qtbot: QtBot, window: MainWindow) -> None:
    with qtbot.waitSignal(window.tutor_client.review_received):
        window._submit_agent_exercise(
            Submission(exercise_id="learn_python_1", answers={"choice": "right"})
        )


def test_learn_round_keeps_a_script_edited_meanwhile(qtbot: QtBot, window: MainWindow) -> None:
    _learn_round(qtbot, window)
    _edit_and_save(window, "# mein eigener Code\n")
    _answer(qtbot, window)
    assert _script(window) == "# mein eigener Code\n"
    assert window.warnings == [T.FILE_CHANGED_TITLE]


def test_learn_round_writes_into_an_unchanged_script(qtbot: QtBot, window: MainWindow) -> None:
    before = _script(window)
    _learn_round(qtbot, window)
    _answer(qtbot, window)
    assert _script(window) != before and window.warnings == []


@pytest.mark.parametrize("changed", [True, False])
def test_mission_code_respects_the_script_state(window: MainWindow, changed: bool) -> None:
    window._mission_target_file = "main.py"
    window._mission_base_text = window._open_script_text()
    if changed:
        _edit_and_save(window, "# mein eigener Code\n")
    window._apply_mission_files(
        ReviewResult(
            correct=True,
            feedback="Richtig",
            generated_files=[GeneratedFile(path="main.py", content="neu\n", explanation="x")],
        )
    )
    assert _script(window) == ("# mein eigener Code\n" if changed else "neu\n")
    assert window._mission_base_text is None
