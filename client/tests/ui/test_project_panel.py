"""The Projekt tab: description, saved state and the way into the other tabs."""

from __future__ import annotations

from pathlib import Path

import pytest
from project_tab_helpers import _ask, _record, make_window
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.domain.project import create_python_project
from learnharness_client.domain.project_plan import MAX_TURNS, ProjectPlan
from learnharness_client.texts import T
from learnharness_client.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch) -> MainWindow:
    return make_window(qtbot, tmp_path, monkeypatch)


def test_project_tab_comes_first_and_has_no_todos(window: MainWindow) -> None:
    assert window.learning_tabs.tabText(0) == "Projekt"
    assert window.learning_tabs.tabText(1) == "LearnAgent"
    assert window.learning_tabs.currentWidget() is window.project_panel
    assert not hasattr(window, "todo_bar") and not hasattr(window.project_panel, "todos")


def test_start_button_leads_to_the_project_mission(qtbot: QtBot, window: MainWindow) -> None:
    sent = _record(window)
    panel = window.project_panel
    assert not panel.build_button.isEnabled()
    panel.description.setPlainText("Ein Mathe-Quiz")
    panel.build_button.click()
    missions = window.mission_panel
    assert window.learning_tabs.currentWidget() is missions and missions.project_card.isVisible()
    missions.project_button.click()
    qtbot.waitUntil(lambda: missions.mission is not None)
    assert sent[0].intent == "mission" and sent[0].message == T.MISSION_PROJECT_WISH
    assert sent[0].project_description == "Ein Mathe-Quiz" and sent[0].mission_from_project


def test_finished_mission_is_remembered_for_the_next(qtbot: QtBot, window: MainWindow) -> None:
    sent = _record(window)
    panel = window.project_panel
    panel.description.setPlainText("Ein Mathe-Quiz")
    missions = window.mission_panel
    window.learning_tabs.setCurrentWidget(missions)
    missions.project_button.click()
    qtbot.waitUntil(lambda: missions.mission is not None)
    title = missions.mission.title
    missions.done = {step.id for step in missions.mission.steps[:-1]}
    missions._render()
    missions.step_button.click()
    assert missions.next_project_button.isVisible()
    assert panel.plan.finished_missions == [title]
    missions.next_project_button.click()
    assert sent[-1].project_done_missions == [title]


def test_each_project_has_its_own_talk(qtbot: QtBot, window: MainWindow, tmp_path: Path) -> None:
    panel = window.project_panel
    first = window.project
    _ask(qtbot, window)
    question = panel.plan.question
    window.open_project(create_python_project(tmp_path, "Rechner"))
    assert panel.description.toPlainText() == "" and panel.plan.question == ""
    assert not window.mission_panel.project_card.isVisible()
    window.open_project(first)
    assert panel.description.toPlainText() == "Ein Mathe-Quiz" and panel.plan.question == question


def test_late_answer_does_not_land_in_another_project(
    qtbot: QtBot, window: MainWindow, tmp_path: Path
) -> None:
    panel = window.project_panel
    panel.description.setPlainText("Quiz")
    with qtbot.waitSignal(window.tutor_client.stream_finished):
        panel.plan_button.click()
        window.open_project(create_python_project(tmp_path, "Anderes"))
    assert panel.plan.question == ""


def test_offline_description_can_still_be_written(window: MainWindow) -> None:
    panel = window.project_panel
    panel.set_available(False)
    panel.description.setPlainText("Quiz")
    assert not panel.plan_button.isEnabled() and panel.build_button.isEnabled()


def test_deleting_a_profile_removes_its_plans(window: MainWindow) -> None:
    profile_id = window.student_profile.profile_id
    window.settings.save_project_plan(profile_id, "p", {"description": "x"})
    window.settings.reset_learning(profile_id)
    assert window.settings.project_plan(profile_id, "p") == {"description": "x"}
    window.settings.delete_student_profile(profile_id)
    assert window.settings.project_plan(profile_id, "p") == {}


def test_plan_tolerates_damage_limits_talk_and_keeps_old_todos() -> None:
    old = [{"text": "Figur bauen", "done": True}]
    plan = ProjectPlan.from_dict(
        {"description": 3, "turns": ["x", {"question": "F", "answer": 1}], "todos": old}
    )
    assert plan.description == "" and plan.turns == []
    assert plan.to_dict()["todos"] == old
    for number in range(MAX_TURNS + 5):
        plan.add_turn(f"Frage {number}", "Antwort")
    assert len(plan.turns) == MAX_TURNS and plan.turns[-1].question == f"Frage {MAX_TURNS + 4}"


def test_project_idea_goes_along_with_learning_requests(qtbot: QtBot, window: MainWindow) -> None:
    sent = _record(window)
    window.project_panel.description.setPlainText("Ein Spiel mit einem Fuchs")
    window.send_tutor_message("Wie fange ich an?")
    window.start_learning_round("Figur bewegen", 1)
    window.request_mission("Münzen sammeln")
    assert not sent[-1].mission_from_project
    assert [message.project_description for message in sent] == ["Ein Spiel mit einem Fuchs"] * 3
    assert sent[0].current_task == window.current_task_id
    assert "Projektidee" in window.tutor_panel.context_label.text()
