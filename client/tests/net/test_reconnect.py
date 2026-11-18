"""WebSocket reconnect backoff and adaptive health-check interval."""

from __future__ import annotations

from learnharness_protocol import HealthStatus
from PyQt6.QtCore import QUrl
from pytestqt.qtbot import QtBot

from learnharness_client.net.connection_monitor import ConnectionMonitor
from learnharness_client.net.fake_tutor_client import FakeTutorClient
from learnharness_client.net.http_tutor_client import HttpTutorClient


def test_backoff_sequence_is_capped_at_30_seconds() -> None:
    delays = [HttpTutorClient.reconnect_delay_ms(attempt) for attempt in range(8)]
    assert delays == [1_000, 2_000, 5_000, 10_000, 30_000, 30_000, 30_000, 30_000]


def test_outage_is_reported_once_and_reconnect_is_scheduled(qtbot: QtBot) -> None:
    client = HttpTutorClient("http://127.0.0.1:9")
    client.session_id = "session"
    client._stream_url = QUrl("ws://127.0.0.1:9/api/v1/sessions/session/stream")
    errors: list[object] = []
    client.error.connect(errors.append)

    client._on_socket_error(None)
    client._on_socket_disconnected()
    assert len(errors) == 1
    assert client._reconnect_timer.isActive()
    assert client._reconnect_timer.interval() == 1_000

    client._reconnect_timer.stop()
    client._on_socket_error(None)
    assert len(errors) == 1
    assert client._reconnect_timer.interval() == 2_000

    client._on_socket_connected()
    assert not client._reconnect_timer.isActive()
    assert client._reconnect_attempt == 0
    client._on_socket_error(None)
    assert len(errors) == 2
    client.cancel()


def test_cancel_stops_reconnecting(qtbot: QtBot) -> None:
    client = HttpTutorClient("http://127.0.0.1:9")
    client.session_id = "session"
    client._stream_url = QUrl("ws://127.0.0.1:9/api/v1/sessions/session/stream")
    client.cancel()
    client._on_socket_disconnected()
    assert not client._reconnect_timer.isActive()


def test_monitor_checks_more_often_after_failure(qtbot: QtBot) -> None:
    client = FakeTutorClient(delay_ms=1)
    monitor = ConnectionMonitor(client, interval_ms=15_000, error_interval_ms=5_000)
    client.simulate_failure = True
    with qtbot.waitSignal(client.health_changed, timeout=1000):
        monitor.start()
    assert monitor.healthy is False
    assert monitor.timer.interval() == 5_000

    client.health_changed.emit(HealthStatus(server_ok=True, model_ok=True))
    assert monitor.healthy is True
    assert monitor.timer.interval() == 15_000
    monitor.stop()
