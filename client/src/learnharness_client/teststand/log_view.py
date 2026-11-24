"""Every AI call of the test stand: what went out, what came back, what the harness did."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QPlainTextEdit,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..ui.theme import monospace_font
from .log_reader import AiCallRow, format_messages, read_calls

COLUMNS = ("Zeit", "Zweck", "Modell", "Status", "Dauer", "Tokens rein/raus")
DETAILS = ("System-Prompt", "Nachrichten", "Antwort der KI", "An das Kind", "Harness und Fehler")


def _status(call: AiCallRow) -> str:
    if not call.ok:
        return "verworfen" if call.response_text else "Fehler"
    return "Eingriff" if call.intervened else "OK"


class LogView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.calls: list[AiCallRow] = []
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.currentCellChanged.connect(lambda row, *_: self._show(row))
        self.follow = QCheckBox("Neuesten Aufruf automatisch anzeigen")
        self.follow.setChecked(True)
        self.details = QTabWidget()
        self.texts: list[QPlainTextEdit] = []
        for title in DETAILS:
            text = QPlainTextEdit()
            text.setReadOnly(True)
            text.setFont(monospace_font())
            text.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
            self.details.addTab(text, title)
            self.texts.append(text)
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.table)
        splitter.addWidget(self.details)
        splitter.setSizes([220, 480])
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.follow)
        layout.addWidget(splitter, 1)

    def poll(self, database: Path) -> None:
        last = self.calls[-1].id if self.calls else 0
        new = read_calls(database, after_id=last)
        for call in new:
            self.calls.append(call)
            row = self.table.rowCount()
            self.table.insertRow(row)
            tokens = f"{call.input_tokens or '–'} / {call.output_tokens or '–'}"
            values = (
                call.created_at[11:],
                call.intent,
                call.model,
                _status(call),
                f"{call.duration_ms or 0} ms",
                tokens,
            )
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        if new and self.follow.isChecked():
            self.table.selectRow(self.table.rowCount() - 1)

    def reset(self) -> None:
        self.calls = []
        self.table.setRowCount(0)
        for text in self.texts:
            text.clear()

    def _show(self, row: int) -> None:
        if not 0 <= row < len(self.calls):
            return
        call = self.calls[row]
        notes = "\n".join(f"• {note}" for note in call.harness_notes)
        problems = "\n\n".join(part for part in (notes, call.error) if part)
        contents = (
            call.system_prompt,
            format_messages(call.messages),
            call.response_text,
            call.delivered_text,
            problems or "Keine Eingriffe.",
        )
        for text, content in zip(self.texts, contents, strict=True):
            text.setPlainText(content)
