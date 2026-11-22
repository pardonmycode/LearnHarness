"""Fixtures of the network tests."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest
from admin_sync_helpers import FakeAdmin, _handler
from PyQt6.QtCore import QSettings

from learnharness_client.config import AppSettings


@pytest.fixture
def admin() -> Iterator[tuple[FakeAdmin, str]]:
    state = FakeAdmin()
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler(state))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield state, f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


@pytest.fixture
def settings(tmp_path: Path) -> AppSettings:
    app_settings = AppSettings()
    app_settings._settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return app_settings
