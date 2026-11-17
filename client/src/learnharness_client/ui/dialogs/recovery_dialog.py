"""Dialog for one recovered unsaved draft."""

from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QPlainTextEdit, QVBoxLayout


class RecoveryDialog(QDialog):
    RESTORE = 2
    DISCARD = 3
    LATER = 0

    def __init__(self, relative_path: str, content: str, parent=None) -> None:
        super().__init__(parent)
        self.choice = self.LATER
        self.setWindowTitle("Ungespeicherte Arbeit gefunden")
        self.resize(700, 480)
        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(f"Für {relative_path} gibt es einen Entwurf von vor dem letzten Beenden.")
        )
        view = QPlainTextEdit(content)
        view.setReadOnly(True)
        layout.addWidget(view)
        buttons = QDialogButtonBox()
        restore = buttons.addButton(
            "Im Editor wiederherstellen", QDialogButtonBox.ButtonRole.AcceptRole
        )
        discard = buttons.addButton(
            "Entwurf verwerfen", QDialogButtonBox.ButtonRole.DestructiveRole
        )
        later = buttons.addButton("Später entscheiden", QDialogButtonBox.ButtonRole.RejectRole)
        restore.clicked.connect(lambda: self._finish(self.RESTORE))
        discard.clicked.connect(lambda: self._finish(self.DISCARD))
        later.clicked.connect(lambda: self._finish(self.LATER))
        layout.addWidget(buttons)

    def _finish(self, choice: int) -> None:
        self.choice = choice
        self.accept() if choice != self.LATER else self.reject()
