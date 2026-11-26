"""Connect this PC to the central administration (teacher area only)."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from learnharness_client import design
from learnharness_client.admin_sync import AdminSync, SyncResult
from learnharness_client.config import AppSettings
from learnharness_client.net.admin_client import AdminClient
from learnharness_client.net.device_pairing import DevicePairing

from ...texts import T
from ..theme import set_state

SYNC_MESSAGES = {
    SyncResult.OK: (T.ADMIN_SYNC_OK, "success"),
    SyncResult.OFFLINE: (T.ADMIN_SYNC_OFFLINE, "error"),
    SyncResult.UNAUTHORIZED: (T.ADMIN_SYNC_UNAUTHORIZED, "error"),
    SyncResult.DISABLED: (T.ADMIN_SYNC_DISABLED, "info"),
}


class AdminDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None, *, suggested_url: str = "") -> None:
        super().__init__(parent)
        self.settings = settings
        self.pairing = DevicePairing(self)
        self.pairing.code_ready.connect(self._code_ready)
        self.pairing.approved.connect(self._approved)
        self.pairing.failed.connect(self._pair_failed)
        self.last_result: SyncResult | None = None
        self.setWindowTitle(T.ADMIN_TITLE)
        self.resize(*design.ADMIN_DIALOG_SIZE)
        layout = QVBoxLayout(self)
        intro = QLabel(T.ADMIN_INTRO)
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")
        layout.addWidget(intro)

        form = QFormLayout()
        # Started with --server: that is usually the administration as well.
        self.url = QLineEdit(settings.admin_url or suggested_url)
        self.url.setPlaceholderText(T.ADMIN_URL_PLACEHOLDER)
        self.url.setAccessibleName(T.ADMIN_URL_A11Y)
        self.token = QLineEdit(settings.admin_token)
        self.token.setEchoMode(QLineEdit.EchoMode.Password)
        self.token.setAccessibleName(T.ADMIN_TOKEN_A11Y)
        self.group = QLineEdit(settings.admin_group)
        self.group.setPlaceholderText(T.ADMIN_GROUP_PLACEHOLDER)
        self.group.setAccessibleName(T.ADMIN_GROUP_A11Y)
        self.device_name = QLineEdit()
        self.device_name.setPlaceholderText(T.ADMIN_DEVICE_NAME_PLACEHOLDER)
        self.device_name.setAccessibleName(T.ADMIN_DEVICE_NAME_A11Y)
        self.device_name.setMaxLength(40)
        self.pair_button = QPushButton(T.ADMIN_PAIR)
        self.pair_button.setProperty("primary", "true")
        self.pair_button.clicked.connect(self._pair)
        pair_row = QHBoxLayout()
        pair_row.addWidget(self.device_name, 1)
        pair_row.addWidget(self.pair_button)
        form.addRow(T.ADMIN_URL, self.url)
        form.addRow(T.ADMIN_DEVICE_NAME, pair_row)
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
        self._say(*SYNC_MESSAGES[result])

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

    def _say(self, text: str, state: str) -> None:
        self.status.setText(text)
        self.status.show()
        set_state(self.status, callout=state)

    def _pair(self) -> None:
        if self.pairing.waiting:  # the button reads "Warten abbrechen" meanwhile
            self.pairing.cancel()
            self._pair_finished()
            self.status.hide()
            return
        if not self.url.text().strip():
            self._say(T.ADMIN_PAIR_NEEDS_URL, "error")
            return
        self.pair_button.setText(T.ADMIN_PAIR_CANCEL)
        self.save_button.setEnabled(False)
        self._say(T.ADMIN_PAIR_SENDING, "info")
        self.pairing.start(self.url.text().strip(), self.device_name.text())

    def _code_ready(self, code: str) -> None:
        self._say(T.ADMIN_PAIR_WAIT.format(code=code), "info")

    def _approved(self, token: str) -> None:
        self._pair_finished()
        self.token.setText(token)
        self.save_and_sync()  # stores address and token and fetches the profiles

    def _pair_failed(self, text: str) -> None:
        self._pair_finished()
        self._say(text, "error")

    def _pair_finished(self) -> None:
        self.pair_button.setText(T.ADMIN_PAIR)
        self.save_button.setEnabled(True)

    def done(self, result: int) -> None:  # noqa: N802 - Qt API
        self.pairing.cancel()  # closing the dialog stops the waiting
        super().done(result)

    def _disconnect(self) -> None:
        self.url.clear()
        self.token.clear()
        self.group.clear()
        self.settings.admin_url = ""
        self.settings.admin_token = ""
        self.settings.admin_group = ""
        self._show(SyncResult.DISABLED)
