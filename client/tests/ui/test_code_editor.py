from __future__ import annotations

from pytestqt.qtbot import QtBot

from learnharness_client.ui.editor.code_editor import CodeEditor


def test_nearby_context_is_limited(qtbot: QtBot) -> None:
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("\n".join(f"line {index}" for index in range(30)))
    editor.goto_line(15)
    excerpt, start = editor.selected_or_nearby_text(radius=2)
    assert start == 13
    assert excerpt.splitlines() == [
        "line 12",
        "line 13",
        "line 14",
        "line 15",
        "line 16",
    ]


def test_error_lines_are_recorded(qtbot: QtBot) -> None:
    editor = CodeEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("one\ntwo\nthree")
    editor.set_error_lines([2, 0, -1])
    assert editor.error_lines == {2}
