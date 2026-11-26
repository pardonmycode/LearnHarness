"""This PC asks for access, shows the code and gets its token once a teacher approves."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest
from pytestqt.qtbot import QtBot

from learnharness_client.config import AppSettings
from learnharness_client.net.device_pairing import DevicePairing
from learnharness_client.texts import T
from learnharness_client.ui.dialogs.admin_dialog import AdminDialog

REQUEST_ID = "a" * 32


class FakeDevices:
    """Approves (or rejects) after a few polls, like a teacher clicking in the admin."""

    def __init__(self) -> None:
        self.token = ""
        self.name = ""
        self.polls = 0
        self.answer = "approved"
        self.create_status = 200

    def state(self, authorization: str) -> str | None:
        if authorization != f"Bearer {self.token}":
            return None
        self.polls += 1
        return "pending" if self.polls < 2 else self.answer


def _handler(devices: FakeDevices) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args: object) -> None:
            pass

        def _reply(self, status: int, body: dict[str, Any]) -> None:
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _status(self, state: str) -> dict[str, Any]:
            return {
                "type": "device_request_status",
                "request_id": REQUEST_ID,
                "code": "4821",
                "status": state,
            }

        def do_POST(self) -> None:  # noqa: N802 - http.server API
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            devices.token, devices.name = body["token"], body["name"]
            if devices.create_status != 200:
                self._reply(devices.create_status, {"type": "error", "code": "x"})
                return
            self._reply(200, self._status("pending"))

        def do_GET(self) -> None:  # noqa: N802 - http.server API
            state = devices.state(self.headers.get("Authorization", ""))
            if state is None:
                self._reply(404, {"type": "error", "code": "unknown_request"})
                return
            self._reply(200, self._status(state))

    return Handler


@pytest.fixture
def devices() -> Iterator[tuple[FakeDevices, str]]:
    state = FakeDevices()
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler(state))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield state, f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def test_pairing_shows_the_code_and_returns_the_token(
    qtbot: QtBot, devices: tuple[FakeDevices, str]
) -> None:
    state, url = devices
    pairing = DevicePairing(poll_ms=20)
    codes: list[str] = []
    pairing.code_ready.connect(codes.append)
    with qtbot.waitSignal(pairing.approved, timeout=5_000) as approved:
        pairing.start(url, "  PC   3 ")
    assert codes == ["4821"] and state.name == "PC 3"
    assert approved.args == [state.token] and len(state.token) >= 32
    assert not pairing.waiting


@pytest.mark.parametrize(
    ("answer", "create_status", "text"),
    [
        ("rejected", 200, T.ADMIN_PAIR_REJECTED),
        ("expired", 200, T.ADMIN_PAIR_EXPIRED),
        ("pending", 429, T.ADMIN_PAIR_FULL),
    ],
)
def test_pairing_reports_why_it_failed(
    qtbot: QtBot, devices: tuple[FakeDevices, str], answer: str, create_status: int, text: str
) -> None:
    state, url = devices
    state.answer, state.create_status = answer, create_status
    pairing = DevicePairing(poll_ms=20)
    with qtbot.waitSignal(pairing.failed, timeout=5_000) as failed:
        pairing.start(url, "PC 3")
    assert failed.args == [text]


def test_unreachable_administration_and_bad_names(qtbot: QtBot) -> None:
    pairing = DevicePairing(poll_ms=20)
    with qtbot.waitSignal(pairing.failed, timeout=5_000) as failed:
        pairing.start("http://127.0.0.1:9", "PC 3")
    assert failed.args == [T.ADMIN_PAIR_OFFLINE]
    with qtbot.waitSignal(pairing.failed, timeout=1_000) as failed:
        pairing.start("http://127.0.0.1:9", " x ")
    assert failed.args == [T.ADMIN_PAIR_NAME]


def test_dialog_pairs_and_saves_the_token(
    qtbot: QtBot, devices: tuple[FakeDevices, str], settings: AppSettings, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    state, url = devices
    dialog = AdminDialog(settings, suggested_url=url)
    qtbot.addWidget(dialog)
    dialog.pairing._timer.setInterval(20)
    synced: list[str] = []
    monkeypatch.setattr(dialog, "save_and_sync", lambda: synced.append(dialog.token.text()))
    assert dialog.url.text() == url
    dialog.device_name.setText("PC 7")
    with qtbot.waitSignal(dialog.pairing.code_ready, timeout=5_000):
        dialog.pair_button.click()
    assert "Code 4821" in dialog.status.text() and dialog.pair_button.text() == T.ADMIN_PAIR_CANCEL
    qtbot.waitUntil(lambda: synced == [state.token], timeout=5_000)
    assert dialog.pair_button.text() == T.ADMIN_PAIR and dialog.save_button.isEnabled()


def test_dialog_needs_an_address_first(qtbot: QtBot, settings: AppSettings) -> None:
    dialog = AdminDialog(settings)
    qtbot.addWidget(dialog)
    dialog.device_name.setText("PC 7")
    dialog.pair_button.click()
    assert dialog.status.text() == T.ADMIN_PAIR_NEEDS_URL and not dialog.pairing.waiting
