"""The helper's questions make the project description clearer."""

from __future__ import annotations

from pathlib import Path

import pytest
from learnharness_protocol import LearningResponse
from project_tab_helpers import _answer, _ask, _record, make_window
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.domain.project_plan import ProjectPlan
from learnharness_client.texts import T
from learnharness_client.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch) -> MainWindow:
    return make_window(qtbot, tmp_path, monkeypatch)


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


def test_emptying_the_description_starts_a_new_talk(qtbot: QtBot, window: MainWindow) -> None:
    _ask(qtbot, window)
    panel = window.project_panel
    _answer(qtbot, window, "Für meine Klasse")
    panel.description.setPlainText("")
    assert panel.plan.turns == [] and panel.plan.question == ""
    assert not panel.helper_card.isVisible()
