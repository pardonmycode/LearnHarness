"""The Projekt tab: a description that gets clearer through the helper's questions."""

from __future__ import annotations

from pathlib import Path

import pytest
from learnharness_protocol import LearningResponse, StudentMessage
from PyQt6.QtCore import QSettings
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import StudentProfile
from learnharness_client.domain.project import create_python_project
from learnharness_client.domain.project_plan import MAX_TURNS, ProjectPlan
from learnharness_client.net.fake_tutor_client import FakeTutorClient
from learnharness_client.texts import T
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


def test_project_tab_comes_first_and_has_no_todos(window: MainWindow) -> None:
    assert window.learning_tabs.tabText(0) == "Projekt"
    assert window.learning_tabs.tabText(1) == "LearnAgent"
    assert window.learning_tabs.currentWidget() is window.project_panel
    assert not hasattr(window, "todo_bar") and not hasattr(window.project_panel, "todos")


def test_helper_asks_one_question_after_the_other(qtbot: QtBot, window: MainWindow) -> None:
    sent = _record(window)
    _ask(qtbot, window)
    panel = window.project_panel
    first = panel.plan.question
    assert panel.helper_card.isVisible() and panel.question.text() == first
    assert sent[0].project_question is None
    _answer(qtbot, window, "Kinder aus meiner Klasse")
    assert sent[1].project_question == first and sent[1].message == "Kinder aus meiner Klasse"
    assert panel.plan.question != first and panel.reply.text() == ""
    _answer(qtbot, window, "Viele Punkte holen")
    assert [turn.answer for turn in sent[2].project_turns] == ["Kinder aus meiner Klasse"]


def test_description_changes_only_when_the_child_accepts(qtbot: QtBot, window: MainWindow) -> None:
    _ask(qtbot, window)
    panel = window.project_panel
    _answer(qtbot, window, "Für meine Klasse")
    proposal = panel.plan.suggestion
    assert panel.suggestion_card.isVisible() and "Für meine Klasse" in proposal
    assert panel.description.toPlainText() == "Ein Mathe-Quiz"
    panel.accept_button.click()
    assert panel.description.toPlainText() == proposal == panel.plan.description
    assert not panel.suggestion_card.isVisible()
    panel.description.undo()
    assert panel.description.toPlainText() == "Ein Mathe-Quiz"


def test_own_edit_replaces_an_old_proposal(qtbot: QtBot, window: MainWindow) -> None:
    _ask(qtbot, window)
    panel = window.project_panel
    _answer(qtbot, window, "Für meine Klasse")
    panel.description.setPlainText("Ganz anders")
    assert panel.plan.suggestion == "" and not panel.suggestion_card.isVisible()


def test_edit_while_waiting_drops_the_late_proposal(window: MainWindow) -> None:
    panel = window.project_panel
    panel.description.setPlainText("Quiz")
    panel._request("Quiz", answer=None)
    panel.description.setPlainText("Rennspiel")
    panel.show_response(
        LearningResponse(mode="project_plan", message="Und?", description_suggestion="Quiz mit X")
    )
    assert panel.plan.suggestion == "" and panel.description.toPlainText() == "Rennspiel"


def test_failed_answer_stays_and_is_not_counted(window: MainWindow) -> None:
    panel = window.project_panel
    panel.description.setPlainText("Quiz")
    panel.plan.question = "Wer spielt?"
    panel.reply.setText("Meine Klasse")
    panel._send_reply()
    panel.show_error("Pause")
    assert panel.reply.text() == "Meine Klasse" and panel.plan.turns == []
    assert panel.open_question is None


def test_other_question_tells_the_helper_what_was_skipped(qtbot: QtBot, window: MainWindow) -> None:
    sent = _record(window)
    _ask(qtbot, window)
    panel = window.project_panel
    first = panel.plan.question
    panel.plan_button.click()
    qtbot.waitUntil(lambda: panel.plan.question != first)
    second = panel.plan.question
    assert sent[1].project_skipped_questions == [first] and sent[1].project_question is None
    assert panel.plan.turns == [] and panel.plan.suggestion == ""
    panel.plan_button.click()
    qtbot.waitUntil(lambda: panel.plan.question != second)
    assert sent[2].project_skipped_questions == [first, second]
    saved = ProjectPlan.from_dict(panel.plan.to_dict())
    assert saved.skipped == [first, second]


def test_failed_skip_is_not_remembered(window: MainWindow) -> None:
    panel = window.project_panel
    panel.description.setPlainText("Quiz")
    panel.plan.question = "Wer spielt?"
    panel._request_from_description()
    assert panel.skipped_questions == ["Wer spielt?"]
    panel.show_error("Pause")
    assert panel.skipped_questions == [] and panel.plan.skipped == []


def test_after_five_answers_it_is_enough(qtbot: QtBot, window: MainWindow) -> None:
    _ask(qtbot, window)
    panel = window.project_panel
    for number in range(5):
        assert not panel.ready_label.isVisible()
        _answer(qtbot, window, f"Antwort {number}")
    assert panel.ready_label.isVisible() and panel.ready_label.text() == T.PLAN_READY
    assert panel.reply_button is not None and panel.helper_card.isVisible()


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
    assert sent[0].project_description == "Ein Mathe-Quiz"


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


def test_emptying_the_description_starts_a_new_talk(qtbot: QtBot, window: MainWindow) -> None:
    _ask(qtbot, window)
    panel = window.project_panel
    _answer(qtbot, window, "Für meine Klasse")
    panel.description.setPlainText("")
    assert panel.plan.turns == [] and panel.plan.question == ""
    assert not panel.helper_card.isVisible()


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
    assert [message.project_description for message in sent] == ["Ein Spiel mit einem Fuchs"] * 3
    assert sent[0].current_task == window.current_task_id
    assert "Projektidee" in window.tutor_panel.context_label.text()
