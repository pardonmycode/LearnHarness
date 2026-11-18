"""Teacher area, LearnAgent changes view and optional autosave."""

from __future__ import annotations

from pathlib import Path

import pytest
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QMessageBox
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import StudentProfile
from learnharness_client.domain.project import GodotProject
from learnharness_client.ui.dialogs.changes_dialog import ChangesDialog, line_changes
from learnharness_client.ui.dialogs.teacher_dialog import PasswordDialog, TeacherDialog
from learnharness_client.ui.editor import editor_tabs as editor_tabs_module
from learnharness_client.ui.editor.editor_tabs import EditorTabs
from learnharness_client.ui.panels.learn_agent_panel import LearnAgentPanel


@pytest.fixture
def settings(tmp_path: Path) -> AppSettings:
    app_settings = AppSettings()
    app_settings._settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return app_settings


def test_teacher_password_is_hashed_and_checked(settings: AppSettings) -> None:
    assert not settings.has_teacher_password()
    settings.set_teacher_password("geheim123")
    stored = str(settings.value("teacher/password"))
    assert "geheim123" not in stored
    assert settings.check_teacher_password("geheim123")
    assert not settings.check_teacher_password("falsch")


def test_password_dialog_requires_matching_long_password(
    qtbot: QtBot, settings: AppSettings
) -> None:
    dialog = PasswordDialog(settings, create=True)
    qtbot.addWidget(dialog)
    dialog.password.setText("kurz")
    dialog.repeat.setText("kurz")
    dialog._accept()
    assert not settings.has_teacher_password()
    dialog.password.setText("lehrerin1")
    dialog.repeat.setText("lehrerin2")
    dialog._accept()
    assert not settings.has_teacher_password()
    dialog.repeat.setText("lehrerin1")
    dialog._accept()
    assert settings.check_teacher_password("lehrerin1")

    unlock = PasswordDialog(settings, create=False)
    qtbot.addWidget(unlock)
    unlock.password.setText("falsch!")
    unlock._accept()
    assert unlock.result() != unlock.DialogCode.Accepted
    assert not unlock.error.isHidden()


def test_teacher_can_set_level_reset_and_delete(
    qtbot: QtBot, settings: AppSettings, monkeypatch: MonkeyPatch
) -> None:
    current = StudentProfile.create("Anna", 1)
    other = StudentProfile.create("Ben", 0)
    settings.save_student_profile(current)
    settings.save_student_profile(other)
    settings.unlock_learning_level(other.profile_id, 6)
    settings.mark_tutorial_seen(other.profile_id)
    monkeypatch.setattr(
        QMessageBox, "question", lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *_args, **_kwargs: None)

    dialog = TeacherDialog(settings, current.profile_id)
    qtbot.addWidget(dialog)
    changes: list[tuple[str, int]] = []
    dialog.level_changed.connect(lambda profile_id, level: changes.append((profile_id, level)))

    dialog.refresh(other.profile_id)
    dialog.level.setValue(3)
    dialog.apply_level.click()
    # Teachers may also lower a level.
    assert settings.max_unlocked_learning_level(other.profile_id) == 3
    assert changes[-1] == (other.profile_id, 3)

    dialog.reset_button.click()
    assert settings.max_unlocked_learning_level(other.profile_id) == 1
    assert not settings.tutorial_seen(other.profile_id)

    dialog.refresh(current.profile_id)
    dialog.delete_button.click()
    assert current.profile_id in {p.profile_id for p in settings.student_profiles}

    dialog.refresh(other.profile_id)
    dialog.delete_button.click()
    assert [p.pseudonym for p in settings.student_profiles] == ["Anna"]


def test_lowering_level_moves_panel_selection(qtbot: QtBot) -> None:
    panel = LearnAgentPanel(max_unlocked_level=5)
    qtbot.addWidget(panel)
    assert panel.current_level == 5
    panel.set_max_unlocked(2)
    assert panel.current_level == 2


def test_line_changes_and_changes_dialog(qtbot: QtBot) -> None:
    old = "extends Node\n\nfunc _ready():\n\tpass\n"
    new = "extends Node2D\n\nfunc _ready():\n\tpass\n\tprint(1)\n"
    changes = line_changes(old, new)
    assert changes.removed == {0}
    assert changes.added == {0, 4}
    dialog = ChangesDialog("player.gd", old, new)
    qtbot.addWidget(dialog)
    assert dialog.old_view.isReadOnly() and dialog.new_view.isReadOnly()
    assert dialog.new_view.toPlainText() == new


def test_changes_toggle_emits(qtbot: QtBot) -> None:
    panel = LearnAgentPanel(max_unlocked_level=1, show_changes=False)
    qtbot.addWidget(panel)
    assert not panel.changes_toggle.isChecked()
    with qtbot.waitSignal(panel.show_changes_toggled) as signal:
        panel.changes_toggle.click()
    assert signal.args == [True]


class StubSettings:
    font_size = 14
    autosave = True


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    (root / "project.godot").write_text('[application]\nconfig/name="T"\n', encoding="utf-8")
    (root / "player.gd").write_bytes(b"extends Node\n")
    return root


def test_agent_write_reports_old_and_new_text(
    qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(editor_tabs_module, "app_data_dir", lambda: tmp_path / "data")
    root = _project(tmp_path)
    settings = StubSettings()
    settings.autosave = False
    tabs = EditorTabs(settings)  # type: ignore[arg-type]
    qtbot.addWidget(tabs)
    tabs.set_project(GodotProject.open(root))
    tabs.open_file(root / "player.gd")
    with qtbot.waitSignal(tabs.generated_file_applied) as signal:
        assert tabs.apply_generated_file("player.gd", "extends Node2D\n")
    assert signal.args == ["player.gd", "extends Node\n", "extends Node2D\n"]


def test_autosave_saves_dirty_files(qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(editor_tabs_module, "app_data_dir", lambda: tmp_path / "data")
    root = _project(tmp_path)
    tabs = EditorTabs(StubSettings())  # type: ignore[arg-type]
    qtbot.addWidget(tabs)
    tabs.set_project(GodotProject.open(root))
    editor = tabs.open_file(root / "player.gd")
    assert editor is not None
    editor.setPlainText("extends Node2D\n")
    assert tabs.quick_save_timer.isActive()
    tabs.autosave_dirty()
    assert (root / "player.gd").read_text(encoding="utf-8") == "extends Node2D\n"

    # A file changed in Godot is not overwritten by autosave.
    editor.setPlainText("extends Sprite2D\n")
    (root / "player.gd").write_text("# aus Godot\n", encoding="utf-8")
    tabs.autosave_dirty()
    assert (root / "player.gd").read_text(encoding="utf-8") == "# aus Godot\n"
