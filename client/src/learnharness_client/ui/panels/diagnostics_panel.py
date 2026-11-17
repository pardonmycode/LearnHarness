"""Technical details kept out of the main child-facing UI."""

from __future__ import annotations

from learnharness_protocol import PROTOCOL_VERSION, HealthStatus
from PyQt6.QtWidgets import QFormLayout, QLabel, QWidget


class DiagnosticsPanel(QWidget):
    def __init__(self, server_url: str, parent=None) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)
        self.url = QLabel(server_url)
        self.protocol = QLabel(PROTOCOL_VERSION)
        self.server = QLabel("Noch nicht geprüft")
        self.model = QLabel("Noch nicht geprüft")
        self.latency = QLabel("–")
        self.last_error = QLabel("–")
        self.last_error.setWordWrap(True)
        layout.addRow("Lernserver:", self.url)
        layout.addRow("Protokoll:", self.protocol)
        layout.addRow("Server:", self.server)
        layout.addRow("Modell:", self.model)
        layout.addRow("Latenz:", self.latency)
        layout.addRow("Letzter Fehler:", self.last_error)

    def set_health(self, health: HealthStatus) -> None:
        self.server.setText("erreichbar" if health.server_ok else "nicht erreichbar")
        self.model.setText("bereit" if health.model_ok else "nicht bereit")
        self.latency.setText(f"{health.latency_ms} ms" if health.latency_ms is not None else "–")

    def set_error(self, code: str) -> None:
        self.last_error.setText(code)
