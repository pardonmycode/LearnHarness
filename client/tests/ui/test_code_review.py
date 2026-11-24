"""The button "Code prüfen lassen" sends the open script and marks the lines."""

from __future__ import annotations

from pathlib import Path

import pytest
from project_tab_helpers import _record, make_window
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.texts import T
from learnharness_client.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch) -> MainWindow:
    return make_window(qtbot, tmp_path, monkeypatch)


def test_review_sends_the_whole_script_and_marks_lines(qtbot: QtBot, window: MainWindow) -> None:
    sent = _record(window)
    window.project_panel.description.setPlainText("Ein Quiz")
    editor = window.editor_tabs.current_editor()
    marked: list[list[int]] = []
    editor.set_error_lines = marked.append
    with qtbot.waitSignal(window.tutor_client.stream_finished, timeout=3000):
        window.tutor_panel.review_button.click()
        assert not window.tutor_panel.review_button.isEnabled()  # no second request meanwhile
    message = sent[0]
    assert message.intent == "review" and message.code_excerpt == editor.toPlainText()
    assert message.project_description == "Ein Quiz"
    assert marked == [[1]]
    assert "Zeile 1" in window.tutor_panel.history.toPlainText()
    assert window.tutor_panel.review_button.isEnabled()


def test_review_needs_an_open_script(window: MainWindow) -> None:
    sent = _record(window)
    editor = window.editor_tabs.current_editor()
    editor.setPlainText("")
    assert window.editor_tabs.save_editor(editor)  # an unsaved file would block closing
    window.tutor_panel.review_button.click()
    assert sent == []
    assert T.TUTOR_REVIEW_NEEDS_FILE in window.tutor_panel.history.toPlainText()


def test_review_keeps_the_hint_progress(qtbot: QtBot, window: MainWindow) -> None:
    window.project_panel.description.setPlainText("Ein Quiz")
    with qtbot.waitSignal(window.tutor_client.stream_finished, timeout=3000):
        window.tutor_panel.hint_button.click()
    with qtbot.waitSignal(window.tutor_client.stream_finished, timeout=3000):
        window.tutor_panel.review_button.click()
    assert window.tutor_panel.hint_progress.value() == 1
