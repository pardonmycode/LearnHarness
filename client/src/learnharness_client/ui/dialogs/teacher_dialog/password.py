"""Password dialog of the teacher area."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from learnharness_client import design
from learnharness_client.config import AppSettings

from ....texts import T
from ...theme import set_state

MIN_PASSWORD_LENGTH = 6


class PasswordDialog(QDialog):
    """Sets a new password (``create=True``) or asks for the existing one."""

    def __init__(self, settings: AppSettings, *, create: bool, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.create = create
        self.setWindowTitle(T.TEACHER_TITLE)
        self.setMinimumWidth(design.TEACHER_PASSWORD_MIN_WIDTH)
        layout = QVBoxLayout(self)
        if create:
            intro = QLabel(T.TEACHER_SET_PASSWORD_INTRO)
            intro.setWordWrap(True)
            intro.setProperty("role", "muted")
            layout.addWidget(intro)
        form = QFormLayout()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setAccessibleName(T.TEACHER_PASSWORD_A11Y)
        form.addRow(T.TEACHER_PASSWORD, self.password)
        self.repeat = QLineEdit()
        self.repeat.setEchoMode(QLineEdit.EchoMode.Password)
        self.repeat.setAccessibleName(T.TEACHER_PASSWORD_REPEAT)
        if create:
            form.addRow(T.TEACHER_PASSWORD_REPEAT, self.repeat)
        layout.addLayout(form)
        self.error = QLabel()
        self.error.setWordWrap(True)
        self.error.hide()
        layout.addWidget(self.error)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok = buttons.button(QDialogButtonBox.StandardButton.Ok)
        assert ok is not None
        ok.setText(T.TEACHER_UNLOCK)
        ok.setProperty("primary", "true")
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _show_error(self, text: str) -> None:
        self.error.setText(text)
        self.error.show()
        set_state(self.error, callout="error")

    def _accept(self) -> None:
        password = self.password.text()
        if self.create:
            if len(password) < MIN_PASSWORD_LENGTH:
                self._show_error(T.TEACHER_PASSWORD_TOO_SHORT)
                return
            if password != self.repeat.text():
                self._show_error(T.TEACHER_PASSWORD_MISMATCH)
                return
            self.settings.set_teacher_password(password)
            self.accept()
            return
        if not self.settings.check_teacher_password(password):
            self.password.clear()
            self._show_error(T.TEACHER_PASSWORD_WRONG)
            return
        self.accept()


def unlock_teacher_area(settings: AppSettings, parent: QWidget | None = None) -> bool:
    """First use sets the password, later uses ask for it."""
    dialog = PasswordDialog(settings, create=not settings.has_teacher_password(), parent=parent)
    return dialog.exec() == QDialog.DialogCode.Accepted
