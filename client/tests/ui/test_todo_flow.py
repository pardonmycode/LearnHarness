"""The project's to-dos drive LearnAgent, missions and tutor."""

from __future__ import annotations

from pathlib import Path

import pytest
from learnharness_protocol import StudentMessage, Submission
from PyQt6.QtCore import QSettings
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import StudentProfile
from learnharness_client.domain.project import create_python_project
from learnharness_client.domain.project_plan import ProjectPlan
from learnharness_client.net.fake_tutor_client import FakeTutorClient
from learnharness_client.ui.editor import editor_tabs as editor_tabs_module
from learnharness_client.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch) -> MainWindow:
    monkeypatch.setattr(editor_tabs_module, "app_data_dir", lambda: tmp_path / "data")
    settings = AppSettings()
    settings._settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.show_agent_changes = False
    profile = StudentProfile.create("Fuchs", 1)
    settings.save_student_profile(profile)
    main = MainWindow(settings, FakeTutorClient(delay_ms=1), profile, server_url="fake")
    qtbot.addWidget(main)
    main.show()
    main.open_project(create_python_project(tmp_path, "Quiz"))
    qtbot.waitUntil(lambda: main.session_id is not None)
    panel = main.project_panel
    panel.description.setPlainText("Ein Mathe-Quiz")
    for text in ("Fragen ausdenken", "Punkte zählen", "Ende bauen"):
        panel.new_todo.setText(text)
        panel.add_button.click()
    return main


def _record(window: MainWindow) -> list[StudentMessage]:
    sent: list[StudentMessage] = []
    original = window.tutor_client.send_message
    window.tutor_client.send_message = lambda message: (sent.append(message), original(message))
    return sent


def test_bar_shows_first_open_todo_in_every_tab(window: MainWindow) -> None:
    assert window.todo_bar.isVisible()
    assert window.todo_bar.todo.text() == "Fragen ausdenken"
    assert "1 VON 3" in window.todo_bar.section.text()
    window.learning_tabs.setCurrentWidget(window.tutor_panel)
    assert window.todo_bar.isVisible()


def test_learn_button_prepares_the_round_for_this_todo(qtbot: QtBot, window: MainWindow) -> None:
    sent = _record(window)
    window.todo_bar.learn_button.click()
    assert window.learning_tabs.currentWidget() is window.learn_agent_panel
    assert window.learn_agent_panel.prompt.toPlainText() == "Fragen ausdenken"
    window.start_learning_round("Fragen ausdenken", 1)
    qtbot.waitUntil(lambda: window.learn_agent_panel.prompt is not None and bool(sent))
    assert sent[0].active_todo == "Fragen ausdenken"
    assert sent[0].project_todos == ["Fragen ausdenken", "Punkte zählen", "Ende bauen"]
    assert sent[0].project_description == "Ein Mathe-Quiz"


def test_written_code_asks_and_done_moves_to_next(qtbot: QtBot, window: MainWindow) -> None:
    with qtbot.waitSignal(window.tutor_client.stream_finished):
        window.start_learning_round("Fragen ausdenken", 1)
    with qtbot.waitSignal(window.tutor_client.review_received):
        window._submit_agent_exercise(
            Submission(exercise_id="learn_python_1", answers={"choice": "right"})
        )
    qtbot.waitUntil(window.todo_bar.question.isVisible)
    assert not window.project_panel.plan.todos[0].done  # the child decides
    window.todo_bar.done_button.click()
    assert window.project_panel.plan.todos[0].done
    assert window.todo_bar.todo.text() == "Punkte zählen"
    assert "2 VON 3" in window.todo_bar.section.text()
    assert not window.todo_bar.question.isVisible()


def test_mission_button_starts_a_mission_for_the_todo(qtbot: QtBot, window: MainWindow) -> None:
    sent = _record(window)
    with qtbot.waitSignal(window.tutor_client.stream_finished):
        window.todo_bar.mission_button.click()
    assert sent[0].intent == "mission" and sent[0].message == "Fragen ausdenken"
    qtbot.waitUntil(lambda: window.mission_panel.mission is not None)
    running = window.mission_panel.mission
    window.todo_bar.mission_button.click()
    assert window.mission_panel.mission is running
    assert len(sent) == 1


def test_finished_mission_asks_about_the_todo(window: MainWindow) -> None:
    window._mission_completed("eigene-mission")
    assert window.todo_bar.question.isVisible()


def test_tutor_hints_follow_the_todo(qtbot: QtBot, window: MainWindow) -> None:
    sent = _record(window)
    window.learning_tabs.setCurrentWidget(window.tutor_panel)
    with qtbot.waitSignal(window.tutor_client.stream_finished, timeout=3000):
        window.tutor_panel.hint_button.click()
    assert sent[0].current_task is None and sent[0].active_todo == "Fragen ausdenken"
    qtbot.waitUntil(lambda: window.tutor_panel.hint_progress.value() == 1)
    window.todo_bar.done_button.click()
    assert window.tutor_panel.hint_progress.value() == 0


def test_child_can_choose_another_todo_and_it_is_saved(window: MainWindow) -> None:
    panel = window.project_panel
    panel.todos.setCurrentRow(2)
    panel.work_button.click()
    assert window.todo_bar.todo.text() == "Ende bauen"
    assert "3 VON 3" in window.todo_bar.section.text()
    saved = ProjectPlan.from_dict(
        window.settings.project_plan(window.student_profile.profile_id, window.project.project_id)
    )
    assert saved.current_todo().text == "Ende bauen"


def test_all_done_and_project_switch(window: MainWindow, tmp_path: Path) -> None:
    for _ in range(3):
        window.todo_bar.done_button.click()
    assert window.todo_bar.todo_text is None
    assert not window.todo_bar.learn_button.isVisible()
    window.open_project(create_python_project(tmp_path, "Leer"))
    assert not window.todo_bar.isVisible()
