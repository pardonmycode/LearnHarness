"""Profile sync against a tiny in-process stand-in for the Django administration."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from PyQt6.QtCore import QSettings
from pytestqt.qtbot import QtBot

from learnharness_client.admin_sync import AdminSync, SyncResult
from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import StudentProfile
from learnharness_client.net.admin_client import AdminClient

TOKEN = "geheim"


class FakeAdmin:
    def __init__(self) -> None:
        self.children: dict[str, dict[str, Any]] = {}
        self.archived: set[str] = set()
        self.requests: list[tuple[str, str, Any]] = []


def _handler(admin: FakeAdmin) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args: object) -> None:
            pass

        def _reply(self, status: int, body: object) -> None:
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _handle(self, method: str) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"null") if length else None
            admin.requests.append((method, self.path, body))
            if self.headers.get("Authorization") != f"Bearer {TOKEN}":
                self._reply(
                    401, {"type": "error", "code": "unauthorized", "message_for_child": "x"}
                )
                return
            parts = self.path.split("?")[0].strip("/").split("/")  # api v1 children [id] [...]
            if parts[3:] == [] and method == "GET":
                profiles = [c for c in admin.children.values()]
                self._reply(200, {"type": "child_profile_list", "profiles": profiles})
            elif parts[3:] == [] and method == "POST":
                if body["profile_id"] in admin.archived:
                    self._reply(
                        409, {"type": "error", "code": "archived", "message_for_child": "x"}
                    )
                    return
                admin.children.setdefault(body["profile_id"], body)
                self._reply(201, admin.children[body["profile_id"]])
            elif len(parts) >= 4 and parts[3] in admin.children:
                child = admin.children[parts[3]]
                if parts[4:] == ["unlock"]:
                    child["max_level"] = max(child["max_level"], body["level"])
                self._reply(200, child)
            else:
                self._reply(
                    404, {"type": "error", "code": "unknown_child", "message_for_child": "x"}
                )

        def do_GET(self) -> None:  # noqa: N802
            self._handle("GET")

        def do_POST(self) -> None:  # noqa: N802
            self._handle("POST")

    return Handler


@pytest.fixture
def admin() -> Iterator[tuple[FakeAdmin, str]]:
    state = FakeAdmin()
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler(state))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield state, f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture
def settings(tmp_path: Path) -> AppSettings:
    app_settings = AppSettings()
    app_settings._settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return app_settings


def _server_child(pseudonym: str, level: int) -> dict[str, Any]:
    return {
        "type": "child_profile",
        "protocol_version": "1.2",
        "profile_id": uuid4().hex,
        "pseudonym": pseudonym,
        "experience_level": 1,
        "max_level": level,
        "group": None,
    }


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
