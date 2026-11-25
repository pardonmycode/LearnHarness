"""The scene goes along with a request and changes only after a correct answer."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from learnharness_protocol import (
    AddNode,
    GeneratedFile,
    ReviewResult,
    SceneEdit,
    SetProperty,
    StudentMessage,
)
from PyQt6.QtCore import QSettings
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import StudentProfile
from learnharness_client.domain.project import GodotProject
from learnharness_client.net.fake_tutor_client import FakeTutorClient
from learnharness_client.texts import T
from learnharness_client.ui.editor import editor_tabs as editor_tabs_module
from learnharness_client.ui.main_window import MainWindow
from learnharness_client.ui.main_window import scenes as scenes_module

FIXTURE = Path(__file__).parents[1] / "fixtures" / "sample_godot_project"
TIMER = SceneEdit(
    path="main.tscn",
    changes=[
        AddNode(parent=".", name="Timer", type="Timer"),
        SetProperty(node="Timer", property="wait_time", value="2.0"),
    ],
)


@pytest.fixture
def window(qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch) -> MainWindow:
    monkeypatch.setattr(editor_tabs_module, "app_data_dir", lambda: tmp_path / "data")
    project = tmp_path / "game"
    shutil.copytree(FIXTURE, project)
    with (project / "project.godot").open("a", encoding="utf-8") as file:
        file.write('\n[input]\n\nspringen={\n"deadzone": 0.5,\n"events": []\n}\n')
    settings = AppSettings()
    settings._settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.show_agent_changes = False
    profile = StudentProfile.create("Fuchs", 1)
    settings.save_student_profile(profile)
    client = FakeTutorClient(delay_ms=1)
    main = MainWindow(settings, client, profile, server_url="fake")
    qtbot.addWidget(main)
    main.show()
    main.open_project(GodotProject.open(project))
    main.editor_tabs.open_file(project / "player.gd")
    qtbot.waitUntil(lambda: main.session_id is not None)
    return main


def _send_learn_round(window: MainWindow) -> StudentMessage:
    sent: list[StudentMessage] = []
    window.tutor_client.send_message = sent.append  # type: ignore[method-assign]
    window.start_learning_round("Alle 2 Sekunden", 3)
    return sent[0]


def _correct_review(window: MainWindow, edit: SceneEdit = TIMER) -> ReviewResult:
    content = window.editor_tabs.current_editor().toPlainText() + "\n# Neu\nvar zeit = 2\n"
    return ReviewResult(
        correct=True,
        feedback="Richtig!",
        generated_files=[GeneratedFile(path="player.gd", content=content, explanation="")],
        scene_edits=[edit],
    )


def test_scene_tree_shows_the_scene_of_the_open_script(window: MainWindow) -> None:
    view = window.scene_view
    assert view.isVisible() and view.found is not None and view.found.relative == "main.tscn"
    root = view.topLevelItem(0)
    assert root is not None and root.text(0) == "Main (Node2D)" + T.SCENE_SCRIPT_MARK
    window.scene_view.show_preview(TIMER)
    root = view.topLevelItem(0)  # the tree is drawn again with the preview
    assert root is not None
    texts = [root.child(i).text(0) for i in range(root.childCount())]
    assert texts == [f"Timer (Timer) · {T.SCENE_NEW}"]


def test_scene_and_input_map_go_along_with_a_request(window: MainWindow) -> None:
    message = _send_learn_round(window)
    assert message.scene is not None and message.scene.path == "main.tscn"
    assert message.scene.nodes[0].type == "Node2D" and message.input_actions == ["springen"]
    assert message.scene.root_name == "Main"
    assert message.project_files == ["main.tscn", "player.gd"]


def test_correct_answer_writes_code_then_scene_with_a_backup(
    window: MainWindow, tmp_path: Path
) -> None:
    _send_learn_round(window)
    window._review_received(_correct_review(window))
    scene = (tmp_path / "game" / "main.tscn").read_text(encoding="utf-8")
    assert '[node name="Timer" type="Timer" parent="."]\nwait_time = 2.0\n' in scene
    assert "var zeit = 2" in (tmp_path / "game" / "player.gd").read_text(encoding="utf-8")
    backups = list((tmp_path / "data" / "backups").rglob("*.bak"))
    assert any(b"Timer" not in item.read_bytes() and b"gd_scene" in item.read_bytes()
               for item in backups)  # fmt: skip
    assert "Gespeicherte Szene neu laden" in window.statusBar().currentMessage()


def test_scene_changed_meanwhile_keeps_code_and_scene(
    window: MainWindow, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    warnings: list[str] = []
    monkeypatch.setattr(
        scenes_module.QMessageBox, "warning", lambda _parent, _title, text: warnings.append(text)
    )
    _send_learn_round(window)
    scene_file = tmp_path / "game" / "main.tscn"
    changed = (
        scene_file.read_text(encoding="utf-8") + '\n[node name="Neu" type="Node" parent="."]\n'
    )
    scene_file.write_text(changed, encoding="utf-8")
    script_before = (tmp_path / "game" / "player.gd").read_text(encoding="utf-8")
    window._review_received(_correct_review(window))
    assert scene_file.read_text(encoding="utf-8") == changed
    assert (tmp_path / "game" / "player.gd").read_text(encoding="utf-8") == script_before
    assert warnings == [T.SCENE_CHANGED_MEANWHILE.format(file="main.tscn")]


def test_edit_for_another_scene_is_refused(window: MainWindow, monkeypatch: MonkeyPatch) -> None:
    warnings: list[str] = []
    monkeypatch.setattr(
        scenes_module.QMessageBox, "warning", lambda _parent, _title, text: warnings.append(text)
    )
    _send_learn_round(window)
    other = TIMER.model_copy(update={"path": "level.tscn"})
    window._review_received(_correct_review(window, other))
    assert warnings == [T.SCENE_DOES_NOT_FIT.format(file="level.tscn")]


def test_mission_step_changes_the_scene_like_the_learn_agent(
    window: MainWindow, tmp_path: Path
) -> None:
    sent: list[StudentMessage] = []
    window.tutor_client.send_message = sent.append  # type: ignore[method-assign]
    window.request_mission_step("mission", "schritt")
    assert sent[0].scene is not None
    window._apply_mission_files(_correct_review(window))
    assert "Timer" in (tmp_path / "game" / "main.tscn").read_text(encoding="utf-8")
