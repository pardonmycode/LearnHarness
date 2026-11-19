"""Tests for the formerly open TODO items: Markdown chat, backups, Godot helpers, startup."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from learnharness_protocol import LearningResponse
from PyQt6.QtGui import QTextDocument
from pytestqt.qtbot import QtBot

from learnharness_client.godot.log_reader import default_log_path, read_recent_errors
from learnharness_client.godot.output_parser import GodotMessage, parse_godot_output
from learnharness_client.godot.syntax_check import SyntaxChecker
from learnharness_client.texts import T
from learnharness_client.ui.dialogs.backup_dialog import BackupDialog, backup_label
from learnharness_client.ui.dialogs.first_start_dialog import normalize_server_url
from learnharness_client.ui.dialogs.tutorial_dialog import TutorialDialog
from learnharness_client.ui.markdown import has_links, insert_markdown, sanitize_markdown
from learnharness_client.ui.panels.problems_panel import Problem, ProblemsPanel
from learnharness_client.ui.panels.tutor_panel import TutorPanel

GODOT_OUTPUT = """\
Godot Engine v4.3.stable.official
SCRIPT ERROR: Parse Error: Expected end of statement after expression, found "Identifier" instead.
          at: GDScript::reload (res://scripts/player.gd:7)
ERROR: Failed to load script "res://scripts/player.gd" with error "Parse error".
   at: load (modules/gdscript/gdscript.cpp:2936)
SCRIPT ERROR: Invalid call. Nonexistent function 'jump' in base 'Node2D'.
          at: _process (res://enemy.gd:12)
"""


def test_markdown_removes_links_images_and_html() -> None:
    text = (
        "**Tipp:** Lies [die Doku](https://example.com) ![Bild](http://x/y.png) "
        "<script>alert(1)</script> <https://evil.example>\n\n[ref]: https://example.com\n"
    )
    cleaned = sanitize_markdown(text)
    assert "https://example.com" not in cleaned
    assert "y.png" not in cleaned
    assert "die Doku" in cleaned and "Bild" in cleaned
    document = QTextDocument()
    from PyQt6.QtGui import QTextCursor

    insert_markdown(QTextCursor(document), text)
    assert not has_links(document)
    assert "<script>" not in document.toHtml()


def test_markdown_keeps_code_blocks_unchanged() -> None:
    text = "Schau:\n```\nvar a = [1](2)\n```\nEnde [x](http://y)"
    cleaned = sanitize_markdown(text)
    assert "var a = [1](2)" in cleaned
    assert cleaned.endswith("Ende x")


def test_tutor_stream_renders_markdown(qtbot: QtBot) -> None:
    panel = TutorPanel()
    qtbot.addWidget(panel)
    panel.begin_stream()
    panel.append_stream_chunk("Das ist **wich")
    panel.append_stream_chunk("tig** – [Link](http://x)")
    panel.finish_stream(LearningResponse(mode="hint", message="Das ist **wichtig**"))
    plain = panel.history.toPlainText()
    assert "wichtig" in plain and "**" not in plain
    assert not has_links(panel.history.document())
    panel.input.setPlainText("Mein **Text**")
    panel._submit()
    # The child's own text is shown exactly as typed.
    assert "Mein **Text**" in panel.history.toPlainText()


def test_godot_output_is_parsed_into_file_and_line() -> None:
    messages = parse_godot_output(GODOT_OUTPUT)
    assert messages == [
        GodotMessage(
            "scripts/player.gd",
            7,
            'Expected end of statement after expression, found "Identifier" instead.',
        ),
        GodotMessage("enemy.gd", 12, "Invalid call. Nonexistent function 'jump' in base 'Node2D'."),
    ]


def test_log_reader_uses_godot_data_dir_and_reads_tail(tmp_path: Path) -> None:
    path = default_log_path("Mein Spiel: Teil 2", data_dir=tmp_path / "Godot")
    assert path == tmp_path / "Godot" / "app_userdata" / "Mein Spiel_ Teil 2" / "logs" / "godot.log"
    assert path is not None
    path.parent.mkdir(parents=True)
    path.write_text("noise\n" * 50_000 + GODOT_OUTPUT, encoding="utf-8")
    assert [m.line for m in read_recent_errors(path)] == [7, 12]
    assert len(read_recent_errors(path, limit=1)) == 1


def test_syntax_check_arguments_and_missing_godot(qtbot: QtBot, tmp_path: Path) -> None:
    script = tmp_path / "scripts" / "player.gd"
    assert SyntaxChecker.arguments(tmp_path, script) == [
        "--headless",
        "--path",
        str(tmp_path),
        "--check-only",
        "--script",
        "res://scripts/player.gd",
    ]
    checker = SyntaxChecker()
    with qtbot.waitSignal(checker.failed, timeout=1000):
        assert not checker.start(str(tmp_path / "missing.exe"), tmp_path, script)
    assert not checker.is_running()


def test_problems_are_not_duplicated_and_can_be_cleared(qtbot: QtBot) -> None:
    panel = ProblemsPanel()
    qtbot.addWidget(panel)
    problem = Problem("player.gd", 3, "Fehler", "Godot-Prüfung")
    assert panel.add_problem(problem)
    assert not panel.add_problem(problem)
    panel.add_problem(Problem("", 0, "Eigener Fehler", "Godot"))
    panel.clear_source("Godot-Prüfung")
    assert [p.source for p in panel.problems()] == ["Godot"]


def test_backup_label_and_restore(qtbot: QtBot, tmp_path: Path, monkeypatch) -> None:
    now = datetime.now(UTC)
    backup = tmp_path / f"{now:%Y%m%dT%H%M%S.%f}Z.bak"
    backup.write_bytes(b"extends Node\n# alt\n")
    assert backup_label(backup).startswith("Heute, ")
    assert backup_label(tmp_path / "kaputt.bak") == "kaputt"

    dialog = BackupDialog("player.gd", [backup])
    qtbot.addWidget(dialog)
    assert dialog.preview.isReadOnly()
    assert dialog.selected_text() == "extends Node\n# alt\n"
    from PyQt6.QtWidgets import QMessageBox

    monkeypatch.setattr(
        QMessageBox, "question", lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes
    )
    dialog.restore_button.click()
    assert dialog.restored_text == "extends Node\n# alt\n"


def test_tutorial_can_be_walked_through(qtbot: QtBot) -> None:
    dialog = TutorialDialog()
    qtbot.addWidget(dialog)
    assert not dialog.back_button.isEnabled()
    for _ in range(len(T.TUTORIAL_STEPS) - 1):
        dialog.next_button.click()
    assert dialog.next_button.text() == T.TUTORIAL_FINISH
    dialog.next_button.click()
    assert dialog.result() == dialog.DialogCode.Accepted


def test_server_url_is_normalized() -> None:
    assert normalize_server_url(" lernserver:8765/ ") == "http://lernserver:8765"
    assert normalize_server_url("https://a.ts.net") == "https://a.ts.net"
    assert normalize_server_url("") == ""
