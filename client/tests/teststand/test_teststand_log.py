"""The test stand reads the prompt log of the local server and shows it."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from pytestqt.qtbot import QtBot

from learnharness_client.config import app_data_dir
from learnharness_client.config.base import DATA_DIR_VARIABLE, SettingsBase
from learnharness_client.teststand.log_reader import format_messages, read_calls
from learnharness_client.teststand.log_view import LogView


def _database(path: Path) -> Path:
    database = path / "server.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE tutor_aicall (id INTEGER PRIMARY KEY, created_at TEXT, intent TEXT, "
            "provider TEXT, model TEXT, ok BOOL, duration_ms INT, input_tokens INT, "
            "output_tokens INT, intervened BOOL, system_prompt TEXT, messages TEXT, "
            "response_text TEXT, delivered_text TEXT, harness_notes TEXT, error TEXT)"
        )
        for number, ok in ((1, True), (2, False)):
            connection.execute(
                "INSERT INTO tutor_aicall VALUES (?, '2026-11-24T10:00:0' || ?, 'mission', "
                "'vllm', 'qwen', ?, 900, 10, 5, 0, 'SYSTEM', ?, 'ANTWORT', 'KIND', ?, ?)",
                (
                    number,
                    number,
                    ok,
                    json.dumps([{"role": "user", "content": "Hallo"}]),
                    json.dumps([] if ok else ["verworfen: Thema"]),
                    "" if ok else "Thema falsch",
                ),
            )
    return database


def test_reader_handles_missing_files_and_tables(tmp_path: Path) -> None:
    assert read_calls(tmp_path / "fehlt.sqlite3") == []
    sqlite3.connect(tmp_path / "leer.sqlite3").close()
    assert read_calls(tmp_path / "leer.sqlite3") == []


def test_reader_returns_new_calls(tmp_path: Path) -> None:
    database = _database(tmp_path)
    calls = read_calls(database)
    assert [call.id for call in calls] == [1, 2] and calls[1].harness_notes == ["verworfen: Thema"]
    assert [call.id for call in read_calls(database, after_id=1)] == [2]
    assert format_messages(calls[0].messages) == "── user ──\nHallo"


def test_view_shows_the_newest_call(qtbot: QtBot, tmp_path: Path) -> None:
    view = LogView()
    qtbot.addWidget(view)
    view.poll(_database(tmp_path))
    assert view.table.rowCount() == 2 and view.table.item(1, 3).text() == "verworfen"
    assert view.texts[0].toPlainText() == "SYSTEM"
    assert "Thema falsch" in view.texts[4].toPlainText()
    view.poll(tmp_path / "server.sqlite3")
    assert view.table.rowCount() == 2


def test_app_data_can_live_in_the_test_stand(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv(DATA_DIR_VARIABLE, str(tmp_path / "client"))
    settings = SettingsBase()
    settings.set_value("x", "1")
    settings._settings.sync()
    assert (tmp_path / "client" / "settings.ini").is_file()
    assert app_data_dir() == tmp_path / "client" / "data"
