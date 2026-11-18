"""Child-friendly external-change conflict dialog."""

from __future__ import annotations

import difflib

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QPlainTextEdit, QVBoxLayout

from ...texts import T


class ConflictDialog(QDialog):
    KEEP_MINE = 2
    LOAD_DISK = 3
    CANCEL = 0

    def __init__(self, mine: str, disk: str, parent=None) -> None:
        super().__init__(parent)
        self.choice = self.CANCEL
        self.setWindowTitle(T.CONFLICT_TITLE)
        self.resize(760, 520)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(T.CONFLICT_INTRO))
        diff = "".join(
            difflib.unified_diff(
                disk.splitlines(keepends=True),
                mine.splitlines(keepends=True),
                fromfile=T.CONFLICT_DISK_VERSION,
                tofile=T.CONFLICT_MY_VERSION,
            )
        )
        view = QPlainTextEdit(diff or T.CONFLICT_SAME)
        view.setReadOnly(True)
        layout.addWidget(view)
        buttons = QDialogButtonBox()
        keep = buttons.addButton(T.CONFLICT_KEEP_MINE, QDialogButtonBox.ButtonRole.AcceptRole)
        load = buttons.addButton(T.CONFLICT_LOAD_DISK, QDialogButtonBox.ButtonRole.DestructiveRole)
        cancel = buttons.addButton(T.CONFLICT_CANCEL, QDialogButtonBox.ButtonRole.RejectRole)
        keep.clicked.connect(lambda: self._finish(self.KEEP_MINE))
        load.clicked.connect(lambda: self._finish(self.LOAD_DISK))
        cancel.clicked.connect(lambda: self._finish(self.CANCEL))
        layout.addWidget(buttons)

    def _finish(self, choice: int) -> None:
        self.choice = choice
        self.accept() if choice != self.CANCEL else self.reject()

    @classmethod
    def choose(cls, mine: str, disk: str, parent=None) -> int:
        dialog = cls(mine, disk, parent)
        dialog.exec()
        return dialog.choice
