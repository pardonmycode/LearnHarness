"""The Projekt tab: idea, suggestions the child decides on, and a saved to-do list."""

from __future__ import annotations

from pathlib import Path

import pytest
from PyQt6.QtCore import QSettings, Qt
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import StudentProfile
from learnharness_client.domain.project import create_python_project
from learnharness_client.domain.project_plan import MAX_TODOS, ProjectPlan
from learnharness_client.net.fake_tutor_client import FakeTutorClient
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
    main.open_project(create_python_project(tmp_path, "Quiz"))
    qtbot.waitUntil(lambda: main.session_id is not None)
    return main


def _plan_once(qtbot: QtBot, window: MainWindow) -> None:
    panel = window.project_panel
    panel.description.setPlainText("Ein Mathe-Quiz")
    panel.plan_button.click()
    qtbot.waitUntil(lambda: bool(panel.plan.suggestions))


def test_tab_sits_next_to_learn_agent(window: MainWindow) -> None:
    assert window.learning_tabs.tabText(0) == "LearnAgent"
    assert window.learning_tabs.tabText(1) == "Projekt"


def test_suggestions_join_the_list_only_when_accepted(qtbot: QtBot, window: MainWindow) -> None:
    _plan_once(qtbot, window)
    panel = window.project_panel
    assert panel.plan.todos == []
    assert panel.plan.question
    first, second = panel.plan.suggestions[:2]
    panel._accept(first)
    panel._reject(second)
    assert [item.text for item in panel.plan.todos] == [first]
    assert first not in panel.plan.suggestions and second not in panel.plan.suggestions


def test_reply_sends_known_todos_and_gets_no_duplicates(qtbot: QtBot, window: MainWindow) -> None:
    _plan_once(qtbot, window)
    panel = window.project_panel
    accepted = panel.plan.suggestions[0]
    panel._accept(accepted)
    panel.reply.setText("Es soll Punkte geben")
    with qtbot.waitSignal(window.tutor_client.stream_finished):
        panel.reply_button.click()
    assert accepted not in panel.plan.suggestions
    assert panel.reply.text() == ""


def test_list_can_be_checked_moved_removed_and_is_saved(qtbot: QtBot, window: MainWindow) -> None:
    panel = window.project_panel
    for text in ("Erstens", "Zweitens"):
        panel.new_todo.setText(text)
        panel.add_button.click()
    panel.todos.item(0).setCheckState(Qt.CheckState.Checked)
    assert panel.progress_label.text() == "1 von 2 erledigt"
    panel.todos.setCurrentRow(1)
    panel.up_button.click()
    assert [item.text for item in panel.plan.todos] == ["Zweitens", "Erstens"]
    panel.remove_button.click()
    assert [item.text for item in panel.plan.todos] == ["Erstens"]
    saved = ProjectPlan.from_dict(
        window.settings.project_plan(window.student_profile.profile_id, window.project.project_id)
    )
    assert [(item.text, item.done) for item in saved.todos] == [("Erstens", True)]


def test_each_project_has_its_own_plan(qtbot: QtBot, window: MainWindow, tmp_path: Path) -> None:
    panel = window.project_panel
    first = window.project
    panel.description.setPlainText("Quiz-Idee")
    panel.new_todo.setText("Fragen sammeln")
    panel.add_button.click()
    window.open_project(create_python_project(tmp_path, "Rechner"))
    assert panel.description.toPlainText() == ""
    assert panel.plan.todos == []
    window.open_project(first)
    assert panel.description.toPlainText() == "Quiz-Idee"
    assert [item.text for item in panel.plan.todos] == ["Fragen sammeln"]


def test_late_answer_does_not_land_in_another_project(
    qtbot: QtBot, window: MainWindow, tmp_path: Path
) -> None:
    panel = window.project_panel
    panel.description.setPlainText("Quiz")
    with qtbot.waitSignal(window.tutor_client.stream_finished):
        panel.plan_button.click()
        window.open_project(create_python_project(tmp_path, "Anderes"))
    assert panel.plan.suggestions == []
    assert panel.plan.question == ""


def test_list_still_works_offline(window: MainWindow) -> None:
    panel = window.project_panel
    panel.description.setPlainText("Quiz")
    panel.set_available(False)
    assert not panel.plan_button.isEnabled()
    panel.new_todo.setText("Offline planen")
    panel.add_button.click()
    assert [item.text for item in panel.plan.todos] == ["Offline planen"]


def test_deleting_a_profile_removes_its_plans(window: MainWindow) -> None:
    profile_id = window.student_profile.profile_id
    window.settings.save_project_plan(profile_id, "p", {"description": "x"})
    window.settings.reset_learning(profile_id)
    assert window.settings.project_plan(profile_id, "p") == {"description": "x"}
    window.settings.delete_student_profile(profile_id)
    assert window.settings.project_plan(profile_id, "p") == {}


def test_plan_tolerates_damaged_data_and_limits_the_list() -> None:
    plan = ProjectPlan.from_dict(
        {"description": 3, "todos": ["x", {"text": 1}, {"text": " a  b "}]}
    )
    assert plan.description == ""
    assert [item.text for item in plan.todos] == ["a b"]
    for number in range(MAX_TODOS + 5):
        plan.add_todo(f"Punkt {number}")
    assert len(plan.todos) == MAX_TODOS
