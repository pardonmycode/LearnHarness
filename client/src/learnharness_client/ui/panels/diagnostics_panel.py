"""Technical details kept out of the main child-facing UI."""

from __future__ import annotations

from learnharness_protocol import PROTOCOL_VERSION, HealthStatus
from PyQt6.QtWidgets import QFormLayout, QLabel, QWidget

from ...texts import T


class DiagnosticsPanel(QWidget):
    def __init__(self, server_url: str, parent=None) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)
        self.url = QLabel(server_url)
        self.protocol = QLabel(PROTOCOL_VERSION)
        self.server = QLabel(T.DIAG_NOT_CHECKED)
        self.model = QLabel(T.DIAG_NOT_CHECKED)
        self.session = QLabel(T.DIAG_NO_SESSION)
        self.latency = QLabel("–")
        self.last_error = QLabel("–")
        self.last_error.setWordWrap(True)
        layout.addRow(T.DIAG_SERVER, self.url)
        layout.addRow(T.DIAG_PROTOCOL, self.protocol)
        layout.addRow(T.DIAG_SERVER_STATE, self.server)
        layout.addRow(T.DIAG_MODEL, self.model)
        layout.addRow(T.DIAG_SESSION, self.session)
        layout.addRow(T.DIAG_LATENCY, self.latency)
        layout.addRow(T.DIAG_LAST_ERROR, self.last_error)

    def set_health(self, health: HealthStatus) -> None:
        self.server.setText(T.DIAG_REACHABLE if health.server_ok else T.DIAG_UNREACHABLE)
        self.model.setText(T.DIAG_READY if health.model_ok else T.DIAG_NOT_READY)
        self.latency.setText(
            T.DIAG_LATENCY_MS.format(ms=health.latency_ms) if health.latency_ms is not None else "–"
        )

    def set_session(self, session_id: str | None) -> None:
        self.session.setText(
            T.DIAG_SESSION_ACTIVE.format(session=session_id[:8])
            if session_id
            else T.DIAG_NO_SESSION
        )

    def set_error(self, code: str) -> None:
        self.last_error.setText(code)
