"""Shared helpers for the tests of the Projekt tab."""

from __future__ import annotations

from pathlib import Path

from learnharness_protocol import StudentMessage
from PyQt6.QtCore import QSettings
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import StudentProfile
from learnharness_client.domain.project import create_python_project
from learnharness_client.net.fake_tutor_client import FakeTutorClient
from learnharness_client.ui.editor import editor_tabs as editor_tabs_module
from learnharness_client.ui.main_window import MainWindow


def make_window(qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch) -> MainWindow:
    monkeypatch.setattr(editor_tabs_module, "app_data_dir", lambda: tmp_path / "data")
    settings = AppSettings()
    settings._settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    profile = StudentProfile.create("Fuchs", 1)
    settings.save_student_profile(profile)
    main = MainWindow(settings, FakeTutorClient(delay_ms=1), profile, server_url="fake")
    qtbot.addWidget(main)
    main.show()
    main.open_project(create_python_project(tmp_path, "Quiz"))
    qtbot.waitUntil(lambda: main.session_id is not None)
    return main


def _record(window: MainWindow) -> list[StudentMessage]:
    sent: list[StudentMessage] = []
    original = window.tutor_client.send_message
    window.tutor_client.send_message = lambda message: (sent.append(message), original(message))
    return sent


def _ask(qtbot: QtBot, window: MainWindow) -> None:
    panel = window.project_panel
    panel.description.setPlainText("Ein Mathe-Quiz")
    panel.plan_button.click()
    qtbot.waitUntil(lambda: bool(panel.plan.question))


def _answer(qtbot: QtBot, window: MainWindow, text: str) -> None:
    panel = window.project_panel
    count = len(panel.plan.turns)
    panel.reply.setText(text)
    panel.reply_button.click()
    qtbot.waitUntil(lambda: len(panel.plan.turns) == count + 1)
