"""Dialog for one recovered unsaved draft."""

from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QPlainTextEdit, QVBoxLayout

from ...texts import T


class RecoveryDialog(QDialog):
    RESTORE = 2
    DISCARD = 3
    LATER = 0

    def __init__(self, relative_path: str, content: str, parent=None) -> None:
        super().__init__(parent)
        self.choice = self.LATER
        self.setWindowTitle(T.RECOVERY_TITLE)
        self.resize(700, 480)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(T.RECOVERY_INTRO.format(file=relative_path)))
        view = QPlainTextEdit(content)
        view.setReadOnly(True)
        layout.addWidget(view)
        buttons = QDialogButtonBox()
        restore = buttons.addButton(T.RECOVERY_RESTORE, QDialogButtonBox.ButtonRole.AcceptRole)
        discard = buttons.addButton(T.RECOVERY_DISCARD, QDialogButtonBox.ButtonRole.DestructiveRole)
        later = buttons.addButton(T.RECOVERY_LATER, QDialogButtonBox.ButtonRole.RejectRole)
        restore.clicked.connect(lambda: self._finish(self.RESTORE))
        discard.clicked.connect(lambda: self._finish(self.DISCARD))
        later.clicked.connect(lambda: self._finish(self.LATER))
        layout.addWidget(buttons)

    def _finish(self, choice: int) -> None:
        self.choice = choice
        self.accept() if choice != self.LATER else self.reject()
