"""Assigned missions from the administration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from admin_sync_helpers import TOKEN, FakeAdmin, _assigned_mission, _server_child
from pytestqt.qtbot import QtBot

from learnharness_client.admin_sync import AdminSync, SyncResult
from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import StudentProfile
from learnharness_client.net.admin_client import AdminClient


def test_missions_are_cached_and_reports_survive_offline(
    qtbot: QtBot, admin: tuple[FakeAdmin, str], settings: AppSettings
) -> None:
    state, url = admin
    child = _server_child("Otter", 1)
    state.children[child["profile_id"]] = child
    state.missions = [_assigned_mission("schatz")]
    profile_id = child["profile_id"]

    online = AdminSync(settings, AdminClient(url, TOKEN))
    received: list[Any] = []
    online.fetch_missions(profile_id, received.append)
    qtbot.waitUntil(lambda: bool(received), timeout=3_000)
    assert [m.id for m in received[0].missions] == ["schatz"]
    assert [m.id for m in online.cached_missions(profile_id).missions] == ["schatz"]

    offline = AdminSync(settings, AdminClient("http://127.0.0.1:9", TOKEN, timeout_ms=1_000))
    offline.report_mission_done(profile_id, "schatz")
    assert settings.pending_mission_reports == {(profile_id, "schatz")}
    assert online.sync_at_start() is SyncResult.OK
    assert settings.pending_mission_reports == set()
    assert state.completed[profile_id] == {"schatz"}

    # A free-wish mission the administration does not know is dropped, not retried forever.
    settings.add_pending_mission_report(profile_id, "eigener-wunsch")
    assert online.sync_at_start() is SyncResult.OK
    assert settings.pending_mission_reports == set()


def test_assigned_mission_runs_in_the_main_window_and_is_reported(
    qtbot: QtBot,
    admin: tuple[FakeAdmin, str],
    settings: AppSettings,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import shutil

    from learnharness_protocol import Submission

    from learnharness_client.domain.project import GodotProject
    from learnharness_client.net.fake_tutor_client import FakeTutorClient
    from learnharness_client.ui.editor import editor_tabs as editor_tabs_module
    from learnharness_client.ui.main_window import MainWindow

    state, url = admin
    profile = StudentProfile.create("Otter", 1)
    settings.save_student_profile(profile)
    settings.show_agent_changes = False
    state.children[profile.profile_id] = {
        **_server_child("Otter", 1),
        "profile_id": profile.profile_id,
    }
    state.missions = [_assigned_mission("schatz")]
    monkeypatch.setattr(editor_tabs_module, "app_data_dir", lambda: tmp_path / "data")
    project = tmp_path / "game"
    shutil.copytree(Path(__file__).parents[1] / "fixtures" / "sample_godot_project", project)

    client = FakeTutorClient(delay_ms=1)
    sync = AdminSync(settings, AdminClient(url, TOKEN))
    window = MainWindow(settings, client, profile, server_url="fake", admin_sync=sync)
    qtbot.addWidget(window)
    window.open_project(GodotProject.open(project))
    window.editor_tabs.open_file(project / "player.gd")
    qtbot.waitUntil(lambda: window.session_id is not None, timeout=3_000)

    panel = window.mission_panel
    qtbot.waitUntil(lambda: panel.assigned_titles() == ["Schatzsuche"], timeout=3_000)
    panel.start_assigned(panel.assigned[0])
    assert panel.progress_label.text() == "Missionsfortschritt: 0 von 2"

    panel.step_button.click()
    qtbot.waitUntil(lambda: panel.exercises.current is not None, timeout=3_000)
    window._submit_mission_exercise(
        Submission(exercise_id="mission_schatz_verstehen", answers={"choice": "right"})
    )
    qtbot.waitUntil(lambda: "verstehen" in panel.done, timeout=3_000)
    panel.step_button.click()  # tried it in Godot
    assert panel.complete

    qtbot.waitUntil(lambda: state.completed.get(profile.profile_id) == {"schatz"}, timeout=3_000)
    qtbot.waitUntil(lambda: panel.assigned_titles() == ["✓ Schatzsuche (geschafft)"], timeout=3_000)
