"""Connect this PC to the central administration (teacher area only)."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from learnharness_client.admin_sync import AdminSync, SyncResult
from learnharness_client.config import AppSettings
from learnharness_client.net.admin_client import AdminClient

from ...texts import T
from ..theme import set_state

SYNC_MESSAGES = {
    SyncResult.OK: (T.ADMIN_SYNC_OK, "success"),
    SyncResult.OFFLINE: (T.ADMIN_SYNC_OFFLINE, "error"),
    SyncResult.UNAUTHORIZED: (T.ADMIN_SYNC_UNAUTHORIZED, "error"),
    SyncResult.DISABLED: (T.ADMIN_SYNC_DISABLED, "info"),
}


class AdminDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.last_result: SyncResult | None = None
        self.setWindowTitle(T.ADMIN_TITLE)
        self.resize(560, 300)
        layout = QVBoxLayout(self)
        intro = QLabel(T.ADMIN_INTRO)
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")
        layout.addWidget(intro)

        form = QFormLayout()
        self.url = QLineEdit(settings.admin_url)
        self.url.setPlaceholderText(T.ADMIN_URL_PLACEHOLDER)
        self.url.setAccessibleName(T.ADMIN_URL_A11Y)
        self.token = QLineEdit(settings.admin_token)
        self.token.setEchoMode(QLineEdit.EchoMode.Password)
        self.token.setAccessibleName(T.ADMIN_TOKEN_A11Y)
        self.group = QLineEdit(settings.admin_group)
        self.group.setPlaceholderText(T.ADMIN_GROUP_PLACEHOLDER)
        self.group.setAccessibleName(T.ADMIN_GROUP_A11Y)
        form.addRow(T.ADMIN_URL, self.url)
        form.addRow(T.ADMIN_TOKEN, self.token)
        form.addRow(T.ADMIN_GROUP, self.group)
        layout.addLayout(form)

        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.hide()
        layout.addWidget(self.status)

        buttons = QDialogButtonBox()
        self.save_button = buttons.addButton(
            T.ADMIN_SAVE_AND_SYNC, QDialogButtonBox.ButtonRole.AcceptRole
        )
        assert self.save_button is not None
        self.save_button.setProperty("primary", "true")
        self.disconnect_button = QPushButton(T.ADMIN_DISCONNECT)
        buttons.addButton(self.disconnect_button, QDialogButtonBox.ButtonRole.ResetRole)
        buttons.addButton(QDialogButtonBox.StandardButton.Close)
        self.save_button.clicked.connect(self.save_and_sync)
        self.disconnect_button.clicked.connect(self._disconnect)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _show(self, result: SyncResult) -> None:
        self.last_result = result
        text, state = SYNC_MESSAGES[result]
        self.status.setText(text)
        self.status.show()
        set_state(self.status, callout=state)

    def save_and_sync(self, client: AdminClient | None = None) -> SyncResult:
        self.settings.admin_url = self.url.text()
        self.settings.admin_token = self.token.text()
        self.settings.admin_group = self.group.text()
        if not self.settings.admin_enabled:
            result = SyncResult.DISABLED
        else:
            if not isinstance(client, AdminClient):  # clicked() passes a bool
                client = AdminClient(self.settings.admin_url, self.settings.admin_token, self)
            self.save_button.setEnabled(False)
            try:
                result = AdminSync(self.settings, client).sync_at_start()
            finally:
                self.save_button.setEnabled(True)
        self._show(result)
        return result

    def _disconnect(self) -> None:
        self.url.clear()
        self.token.clear()
        self.group.clear()
        self.settings.admin_url = ""
        self.settings.admin_token = ""
        self.settings.admin_group = ""
        self._show(SyncResult.DISABLED)
