"""Editing Python: indentation, highlighting, and the LearnAgent writing Python only."""

from __future__ import annotations

from learnharness_protocol import StudentMessage, Submission
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument
from pytestqt.qtbot import QtBot

from learnharness_client.net.fake_tutor_client import FakeTutorClient
from learnharness_client.ui.editor.code_editor import CodeEditor
from learnharness_client.ui.editor.python_highlighter import PythonHighlighter


def _editor(qtbot: QtBot, text: str = "") -> CodeEditor:
    editor = CodeEditor(language="python")
    qtbot.addWidget(editor)
    editor.setPlainText(text)
    editor.adopt_indentation(text)
    return editor


def test_enter_after_colon_indents_four_spaces(qtbot: QtBot) -> None:
    editor = _editor(qtbot, "def main():")
    editor.moveCursor(editor.textCursor().MoveOperation.End)
    qtbot.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText() == "def main():\n    "
    qtbot.keyClick(editor, Qt.Key.Key_Return)
    assert editor.toPlainText().endswith("\n    \n    ")


def test_tab_and_backtab_use_spaces(qtbot: QtBot) -> None:
    editor = _editor(qtbot, "x = 1")
    qtbot.keyClick(editor, Qt.Key.Key_Tab)
    assert editor.toPlainText() == "    x = 1"
    qtbot.keyClick(editor, Qt.Key.Key_Backtab)
    assert editor.toPlainText() == "x = 1"


def test_file_with_tabs_keeps_tabs(qtbot: QtBot) -> None:
    editor = _editor(qtbot, "if x:\n\ty = 1")
    assert editor.indent_unit == "\t"


def test_block_outdent_removes_spaces(qtbot: QtBot) -> None:
    editor = _editor(qtbot, "    a\n    b")
    editor.selectAll()
    qtbot.keyClick(editor, Qt.Key.Key_Backtab)
    assert editor.toPlainText() == "a\nb"


def _format_at(document: QTextDocument, line: int, column: int):
    block = document.findBlockByNumber(line)
    position = column
    for item in block.layout().formats():
        if item.start <= position < item.start + item.length:
            return item.format
    return None


def test_hash_in_string_is_no_comment(qtbot: QtBot) -> None:
    document = QTextDocument('x = "a # b"  # echt')
    highlighter = PythonHighlighter(document)
    highlighter.rehighlight()
    in_string = _format_at(document, 0, 7)
    comment = _format_at(document, 0, 14)
    assert in_string is not None and not in_string.fontItalic()
    assert comment is not None and comment.fontItalic()


def test_triple_quotes_span_lines(qtbot: QtBot) -> None:
    document = QTextDocument("a = '''eins\nzwei\ndrei'''\nb = 1")
    highlighter = PythonHighlighter(document)
    highlighter.rehighlight()
    assert document.findBlockByNumber(0).userState() == 2
    assert document.findBlockByNumber(1).userState() == 2
    assert document.findBlockByNumber(2).userState() == 0


def _message(**fields) -> StudentMessage:
    return StudentMessage(
        language="python", session_id="s", project_id="p", file="main.py", **fields
    )


def test_fake_server_writes_python_into_python_projects(qtbot: QtBot) -> None:
    client = FakeTutorClient(delay_ms=1)
    with qtbot.waitSignal(client.stream_finished) as answer:
        client.send_message(_message(intent="learn", learning_level=1, message="Begrüßung"))
    exercise = answer.args[0].exercise
    with qtbot.waitSignal(client.review_received) as review:
        client.submit_exercise(Submission(exercise_id=exercise.id, answers={"choice": "right"}))
    generated = review.args[0].generated_files
    assert [item.path for item in generated] == ["main.py"]
    compile(generated[0].content, "main.py", "exec")


def test_saved_godot_mission_writes_no_gdscript_into_python(qtbot: QtBot) -> None:
    client = FakeTutorClient(delay_ms=1)
    with qtbot.waitSignal(client.stream_finished) as answer:
        client.send_message(
            _message(
                intent="mission_step",
                mission_id="double_jump",
                mission_step_id="condition",
                message="condition",
            )
        )
    exercise = answer.args[0].exercise
    with qtbot.waitSignal(client.review_received) as review:
        client.submit_exercise(Submission(exercise_id=exercise.id, answers={"choice": "right"}))
    assert review.args[0].generated_files == []
