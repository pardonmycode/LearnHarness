"""Periodic health checks without blocking editor work."""

from __future__ import annotations

from PyQt6.QtCore import QObject, QTimer

from .tutor_client import TutorClient


class ConnectionMonitor(QObject):
    def __init__(self, client: TutorClient, parent=None, *, interval_ms: int = 15_000) -> None:
        super().__init__(parent)
        self.client = client
        self.timer = QTimer(self)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self.client.check_health)

    def start(self) -> None:
        self.client.check_health()
        self.timer.start()

    def stop(self) -> None:
        self.timer.stop()
