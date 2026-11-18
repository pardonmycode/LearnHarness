"""First start: enter and test the learning-server address once."""

from __future__ import annotations

import json

from learnharness_protocol import HealthStatus
from pydantic import ValidationError
from PyQt6.QtCore import QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from learnharness_client.config import AppSettings

from ...texts import T
from ..theme import set_state


def normalize_server_url(text: str) -> str:
    url = text.strip().rstrip("/")
    if url and "://" not in url:
        url = f"http://{url}"
    return url


class FirstStartDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.network = QNetworkAccessManager(self)
        self._reply: QNetworkReply | None = None
        self.setWindowTitle(T.FIRST_START_TITLE)
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        heading = QLabel(T.FIRST_START_TITLE)
        heading.setProperty("role", "heading")
        intro = QLabel(T.FIRST_START_INTRO)
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")
        layout.addWidget(heading)
        layout.addWidget(intro)

        form = QFormLayout()
        address_row = QHBoxLayout()
        self.address = QLineEdit(settings.server_url)
        self.address.setPlaceholderText("http://lernserver:8765")
        self.address.setAccessibleName(T.FIRST_START_ADDRESS_A11Y)
        self.test_button = QPushButton(T.FIRST_START_TEST)
        address_row.addWidget(self.address, 1)
        address_row.addWidget(self.test_button)
        form.addRow(T.FIRST_START_ADDRESS, address_row)
        layout.addLayout(form)

        self.result = QLabel()
        self.result.setWordWrap(True)
        self.result.hide()
        layout.addWidget(self.result)

        self.fake_server = QCheckBox(T.FIRST_START_FAKE)
        self.fake_server.setChecked(settings.use_fake_server)
        layout.addWidget(self.fake_server)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        ok = buttons.button(QDialogButtonBox.StandardButton.Ok)
        assert ok is not None
        ok.setText(T.FIRST_START_DONE)
        ok.setProperty("primary", "true")
        buttons.accepted.connect(self._save)
        layout.addWidget(buttons)

        self.test_button.clicked.connect(self.test_connection)
        self.address.returnPressed.connect(self.test_connection)

    def _show_result(self, text: str, state: str) -> None:
        self.result.setText(text)
        self.result.show()
        set_state(self.result, callout=state)

    def test_connection(self) -> None:
        url = normalize_server_url(self.address.text())
        if not url:
            self._show_result(T.FIRST_START_FAILED, "error")
            return
        if self._reply is not None:
            self._reply.abort()
        self.test_button.setEnabled(False)
        self._show_result(T.FIRST_START_TESTING, "neutral")
        request = QNetworkRequest(QUrl(f"{url}/api/v1/health"))
        request.setTransferTimeout(5_000)
        reply = self.network.get(request)
        self._reply = reply
        reply.finished.connect(lambda current=reply: self._test_finished(current))

    def _test_finished(self, reply: QNetworkReply) -> None:
        if reply is not self._reply:
            reply.deleteLater()
            return
        self._reply = None
        self.test_button.setEnabled(True)
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                raise ValueError("network")
            health = HealthStatus.model_validate(json.loads(bytes(reply.readAll()).decode()))
        except (ValueError, ValidationError, UnicodeDecodeError):
            self._show_result(T.FIRST_START_FAILED, "error")
        else:
            if health.server_ok and health.model_ok:
                self._show_result(T.FIRST_START_OK, "success")
                self.fake_server.setChecked(False)
            else:
                self._show_result(T.FIRST_START_SERVER_ONLY, "info")
        finally:
            reply.deleteLater()

    def _save(self) -> None:
        url = normalize_server_url(self.address.text())
        if url:
            self.settings.server_url = url
        self.settings.use_fake_server = self.fake_server.isChecked()
        self.settings.first_start_done = True
        self.accept()
