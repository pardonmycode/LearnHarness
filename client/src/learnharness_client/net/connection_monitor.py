"""Periodic health checks without blocking editor work."""

from __future__ import annotations

from learnharness_protocol import HealthStatus
from PyQt6.QtCore import QObject, QTimer

from .tutor_client import TutorClient


class ConnectionMonitor(QObject):
    """Checks every 15 s; after a failed check more often (5 s) until the server is back."""

    def __init__(
        self,
        client: TutorClient,
        parent: QObject | None = None,
        *,
        interval_ms: int = 15_000,
        error_interval_ms: int = 5_000,
    ) -> None:
        super().__init__(parent)  # type: ignore[arg-type]  # see qtcompat
        self.client = client
        self.interval_ms = interval_ms
        self.error_interval_ms = error_interval_ms
        self.healthy: bool | None = None
        self.timer = QTimer(self)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self.client.check_health)
        self.client.health_changed.connect(self._health_changed)

    def start(self) -> None:
        self.client.check_health()
        self.timer.start()

    def stop(self) -> None:
        self.timer.stop()

    def _health_changed(self, health: HealthStatus) -> None:
        self.healthy = bool(health.server_ok and health.model_ok)
        interval = self.interval_ms if self.healthy else self.error_interval_ms
        if interval != self.timer.interval():
            self.timer.setInterval(interval)
