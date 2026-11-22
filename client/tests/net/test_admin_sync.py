"""Syncing profiles and level unlocks."""

from __future__ import annotations

from admin_sync_helpers import TOKEN, FakeAdmin, _server_child
from pytestqt.qtbot import QtBot

from learnharness_client.admin_sync import AdminSync, SyncResult
from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import StudentProfile
from learnharness_client.net.admin_client import AdminClient


def test_sync_registers_pulls_and_removes(
    qtbot: QtBot, admin: tuple[FakeAdmin, str], settings: AppSettings
) -> None:
    state, url = admin
    local = StudentProfile.create("Fuchs", 0)
    settings.save_student_profile(local)
    settings.unlock_learning_level(local.profile_id, 3)
    teacher_child = _server_child("Eule", 5)
    state.children[teacher_child["profile_id"]] = teacher_child
    gone = StudentProfile.create("Biber", 0)
    settings.save_student_profile(gone, remember=False)
    settings.set_synced_profile_ids({gone.profile_id})  # synced before, deleted by the teacher

    sync = AdminSync(settings, AdminClient(url, TOKEN))
    assert sync.sync_at_start() is SyncResult.OK

    # Local profile uploaded with its level, teacher's child arrived, deleted child removed.
    assert state.children[local.profile_id]["max_level"] == 3
    names = sorted(p.pseudonym for p in settings.student_profiles)
    assert names == ["Eule", "Fuchs"]
    assert settings.max_unlocked_learning_level(teacher_child["profile_id"]) == 5
    assert settings.last_profile_id == local.profile_id  # the login choice stays

    # The teacher lowers the level centrally: the next sync takes it over.
    state.children[local.profile_id]["max_level"] = 2
    assert sync.sync_at_start() is SyncResult.OK
    assert settings.max_unlocked_learning_level(local.profile_id) == 2


def test_pending_unlock_survives_offline_and_is_sent_later(
    qtbot: QtBot, admin: tuple[FakeAdmin, str], settings: AppSettings
) -> None:
    state, url = admin
    child = _server_child("Igel", 1)
    state.children[child["profile_id"]] = child

    offline = AdminSync(settings, AdminClient("http://127.0.0.1:9", TOKEN, timeout_ms=1_000))
    offline.unlock(child["profile_id"], 4)  # remembered before the request even leaves
    assert settings.pending_unlocks == {child["profile_id"]: 4}
    assert offline.sync_at_start() is SyncResult.OFFLINE

    online = AdminSync(settings, AdminClient(url, TOKEN))
    assert online.sync_at_start() is SyncResult.OK
    assert settings.pending_unlocks == {}
    assert state.children[child["profile_id"]]["max_level"] == 4
    assert settings.max_unlocked_learning_level(child["profile_id"]) == 4


def test_async_unlock_reports_server_level(
    qtbot: QtBot, admin: tuple[FakeAdmin, str], settings: AppSettings
) -> None:
    state, url = admin
    child = _server_child("Luchs", 6)
    state.children[child["profile_id"]] = child
    sync = AdminSync(settings, AdminClient(url, TOKEN))
    levels: list[int] = []
    sync.unlock(child["profile_id"], 3, levels.append)
    qtbot.waitUntil(lambda: bool(levels), timeout=3_000)
    assert levels == [6]  # never lower than what the server already has
    assert settings.pending_unlocks == {}


def test_wrong_token_and_archived_profiles(
    qtbot: QtBot, admin: tuple[FakeAdmin, str], settings: AppSettings
) -> None:
    state, url = admin
    local = StudentProfile.create("Dachs", 0)
    settings.save_student_profile(local)
    assert AdminSync(settings, AdminClient(url, "falsch")).sync_at_start() is (
        SyncResult.UNAUTHORIZED
    )
    state.archived.add(local.profile_id)
    assert AdminSync(settings, AdminClient(url, TOKEN)).sync_at_start() is SyncResult.OK
    assert settings.student_profiles == []


def test_from_settings_needs_url_and_token(settings: AppSettings) -> None:
    assert AdminSync.from_settings(settings) is None
    settings.admin_url = "http://verwaltung:8000/"
    settings.admin_token = " abc "
    assert settings.admin_url == "http://verwaltung:8000"
    assert settings.admin_token == "abc"
    assert AdminSync.from_settings(settings) is not None
