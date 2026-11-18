"""Read-only view of pre-save backups with an explicit restore button."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from ...texts import T
from ..editor.gdscript_highlighter import GDScriptHighlighter
from ..theme import monospace_font


def backup_label(path: Path) -> str:
    """Turn ``20261118T093012.123456Z.bak`` into a local, child-friendly time."""
    try:
        stamp = datetime.strptime(path.stem, "%Y%m%dT%H%M%S.%fZ").replace(tzinfo=UTC)
    except ValueError:
        return path.stem
    local = stamp.astimezone()
    today = datetime.now().astimezone().date()
    if local.date() == today:
        return T.BACKUP_TODAY.format(time=f"{local:%H:%M:%S}")
    return T.BACKUP_DATE.format(date=f"{local:%d.%m.%Y, %H:%M}")


class BackupDialog(QDialog):
    """Shows older versions; nothing changes unless the child presses restore."""

    def __init__(self, file_name: str, backups: list[Path], parent=None) -> None:
        super().__init__(parent)
        self.restored_text: str | None = None
        self.setWindowTitle(T.BACKUP_TITLE.format(file=file_name))
        self.resize(900, 560)
        layout = QVBoxLayout(self)
        intro = QLabel(T.BACKUP_INTRO)
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")
        layout.addWidget(intro)

        row = QHBoxLayout()
        self.versions = QListWidget()
        self.versions.setAccessibleName(T.BACKUP_LIST_A11Y)
        self.versions.setMaximumWidth(230)
        for path in backups:
            item = QListWidgetItem(backup_label(path))
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setToolTip(path.name)
            self.versions.addItem(item)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setObjectName("codeView")
        self.preview.setFont(monospace_font())
        self.preview.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.preview.setAccessibleName(T.BACKUP_PREVIEW_A11Y)
        self._highlighter = GDScriptHighlighter(self.preview.document())
        row.addWidget(self.versions)
        row.addWidget(self.preview, 1)
        layout.addLayout(row, 1)

        buttons = QDialogButtonBox()
        self.restore_button = QPushButton(T.BACKUP_RESTORE)
        self.restore_button.setEnabled(False)
        buttons.addButton(self.restore_button, QDialogButtonBox.ButtonRole.ActionRole)
        close = buttons.addButton(T.BACKUP_CLOSE, QDialogButtonBox.ButtonRole.RejectRole)
        assert close is not None
        close.setProperty("primary", "true")
        buttons.rejected.connect(self.reject)
        self.restore_button.clicked.connect(self._restore)
        layout.addWidget(buttons)

        self.versions.currentItemChanged.connect(self._show_version)
        if self.versions.count():
            self.versions.setCurrentRow(0)

    def _show_version(self, item: QListWidgetItem | None) -> None:
        if item is None:
            self.preview.clear()
            self.restore_button.setEnabled(False)
            return
        try:
            data = Path(str(item.data(Qt.ItemDataRole.UserRole))).read_bytes()
            text = data.decode("utf-8-sig", errors="replace")
        except OSError as exc:
            text = T.BACKUP_UNREADABLE.format(error=exc)
            self.restore_button.setEnabled(False)
        else:
            self.restore_button.setEnabled(True)
        self.preview.setPlainText(text)

    def selected_text(self) -> str:
        return self.preview.toPlainText()

    def _restore(self) -> None:
        answer = QMessageBox.question(
            self,
            T.BACKUP_CONFIRM_TITLE,
            T.BACKUP_CONFIRM,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.restored_text = self.selected_text()
            self.accept()
