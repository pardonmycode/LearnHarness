"""End-to-end through the main window with the built-in fake server."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from learnharness_protocol import Submission
from PyQt6.QtCore import QSettings
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import StudentProfile
from learnharness_client.domain.project import GodotProject
from learnharness_client.net.fake_tutor_client import FakeTutorClient
from learnharness_client.ui.editor import editor_tabs as editor_tabs_module
from learnharness_client.ui.main_window import MainWindow
from learnharness_client.ui.panels.mission_panel import MissionPanel

FIXTURE = Path(__file__).parents[1] / "fixtures" / "sample_godot_project"


@pytest.fixture
def window(qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch) -> MainWindow:
    monkeypatch.setattr(editor_tabs_module, "app_data_dir", lambda: tmp_path / "data")
    project = tmp_path / "game"
    shutil.copytree(FIXTURE, project)
    settings = AppSettings()
    settings._settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.show_agent_changes = False
    profile = StudentProfile.create("Fuchs", 1)
    settings.save_student_profile(profile)
    client = FakeTutorClient(delay_ms=1)
    main = MainWindow(settings, client, profile, server_url="fake")
    qtbot.addWidget(main)
    main.open_project(GodotProject.open(project))
    main.editor_tabs.open_file(project / "player.gd")
    with qtbot.waitSignal(client.session_started, timeout=2_000):
        client.start_session("p", profile.profile_id, profile.pseudonym, 1)
    qtbot.waitUntil(lambda: main.session_id is not None)
    return main


def test_explainer_asks_about_selected_code(qtbot: QtBot, window: MainWindow) -> None:
    window.explain_selection()
    panel = window.explain_panel
    assert window.learning_tabs.currentWidget() is panel
    assert panel.code and panel.question_texts()

    panel.ask("Was macht velocity.x = speed?")
    qtbot.waitUntil(lambda: panel.exercises.current is not None, timeout=3_000)
    assert "waagerecht" in panel.answer.text()

    window._submit_explain_exercise(
        Submission(exercise_id="explain_velocity", answers={"choice": "right"})
    )
    qtbot.waitUntil(lambda: not panel.feedback.isHidden(), timeout=3_000)
    assert "verstanden" in panel.feedback.text()


def test_skill_focus_round_writes_code_after_correct_answer(
    qtbot: QtBot, window: MainWindow
) -> None:
    qtbot.waitUntil(lambda: window.learn_agent_panel.current_focus == "conditions", timeout=3_000)
    window.start_learning_round("Mach was mit if", 1)
    agent = window.learn_agent_panel
    qtbot.waitUntil(lambda: agent.exercise_widget is not None, timeout=3_000)
    window._submit_agent_exercise(
        Submission(
            exercise_id="learn_focus_conditions_1", answers={"first": "if", "second": "else"}
        )
    )
    editor = window.editor_tabs.current_editor()
    assert editor is not None
    qtbot.waitUntil(lambda: "else:" in editor.toPlainText(), timeout=3_000)
    assert window.settings.max_unlocked_learning_level(window.student_profile.profile_id) == 2


def test_mission_runs_step_by_step_and_is_remembered(qtbot: QtBot, window: MainWindow) -> None:
    panel = window.mission_panel
    panel.request_mission("Ich will einen Doppelsprung")
    qtbot.waitUntil(lambda: panel.mission is not None, timeout=3_000)
    assert panel.mission is not None and panel.mission.id == "double_jump"
    assert panel.progress_label.text() == "Missionsfortschritt: 0 von 4"

    answers = {
        "understand": {"choice": "right"},
        "variable": {"blank": "var"},
        "condition": {"blank": "and"},
    }
    for step_id, answer in answers.items():
        panel.step_button.click()
        qtbot.waitUntil(lambda: panel.exercises.current is not None, timeout=3_000)
        window._submit_mission_exercise(
            Submission(exercise_id=f"mission_double_jump_{step_id}", answers=answer)
        )
        qtbot.waitUntil(lambda step=step_id: step in panel.done, timeout=3_000)

    editor = window.editor_tabs.current_editor()
    assert editor is not None
    qtbot.waitUntil(lambda: "jumps_left" in editor.toPlainText(), timeout=3_000)
    assert panel.step_button.text().startswith("Weiter zu Schritt 4")
    panel.step_button.click()
    assert "Godot" in panel.message.text()  # instructions for the last step
    assert panel.help_button.isVisibleTo(panel)

    panel.step_button.click()  # "Hat geklappt"
    assert panel.complete
    assert "Mission erfüllt" in panel.message.text()

    saved = window.settings.mission_progress(window.student_profile.profile_id)
    restored = MissionPanel()
    qtbot.addWidget(restored)
    restored.restore(saved)
    assert restored.complete and restored.mission is not None


def test_wrong_mission_answer_keeps_the_step_open(qtbot: QtBot, window: MainWindow) -> None:
    panel = window.mission_panel
    panel.request_mission("Münzen")
    qtbot.waitUntil(lambda: panel.mission is not None, timeout=3_000)
    panel.step_button.click()
    qtbot.waitUntil(lambda: panel.exercises.current is not None, timeout=3_000)
    window._submit_mission_exercise(
        Submission(exercise_id="mission_coins_understand", answers={"choice": "wrong"})
    )
    qtbot.waitUntil(lambda: "Noch nicht" in panel.message.text(), timeout=3_000)
    assert panel.done == set()
