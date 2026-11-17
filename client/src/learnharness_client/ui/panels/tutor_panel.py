"""Tutor conversation without any apply-to-editor action."""

from __future__ import annotations

import logging

from learnharness_protocol import LearningResponse
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QKeyEvent, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..theme import colors

LOG = logging.getLogger(__name__)


class MessageInput(QPlainTextEdit):
    submit_requested = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 - Qt API
        if (
            event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.submit_requested.emit()
            return
        super().keyPressEvent(event)


class TutorPanel(QWidget):
    message_submitted = pyqtSignal(str)
    next_hint_requested = pyqtSignal()
    cancel_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        heading = QLabel("Lernhelfer")
        heading.setProperty("role", "heading")
        layout.addWidget(heading)
        self.context_label = QLabel("Dem Lernhelfer wird nur ein kleiner Codeausschnitt gezeigt.")
        self.context_label.setWordWrap(True)
        self.context_label.setProperty("role", "small")
        self.history = QTextBrowser()
        self.history.setOpenExternalLinks(False)
        self.history.setOpenLinks(False)
        self.history.setAccessibleName("Gespräch mit dem Lernhelfer")
        self.input = MessageInput()
        self.input.setPlaceholderText("Schreibe deine Frage … (Strg+Enter sendet)")
        self.input.setMaximumHeight(110)
        self.input.setAccessibleName("Frage an den Lernhelfer")
        self.counter = QLabel("0 / 2000")
        self.hint_progress = QProgressBar()
        self.hint_progress.setRange(0, 4)
        self.hint_progress.setValue(0)
        self.hint_progress.setFormat("Hinweisstufe %v von %m")
        buttons = QHBoxLayout()
        self.send_button = QPushButton("Frage senden")
        self.send_button.setProperty("primary", "true")
        self.hint_button = QPushButton("Nächster Hinweis")
        self.stop_button = QPushButton("Stopp")
        self.stop_button.setEnabled(False)
        buttons.addWidget(self.send_button)
        buttons.addWidget(self.hint_button)
        buttons.addWidget(self.stop_button)
        buttons.addStretch(1)
        buttons.addWidget(self.counter)
        layout.addWidget(self.context_label)
        layout.addWidget(self.history, 1)
        layout.addWidget(self.hint_progress)
        layout.addWidget(self.input)
        layout.addLayout(buttons)
        self.send_button.clicked.connect(self._submit)
        self.input.submit_requested.connect(self._submit)
        self.hint_button.clicked.connect(self.next_hint_requested)
        self.stop_button.clicked.connect(self.cancel_requested)
        self.input.textChanged.connect(self._update_counter)
        self._stream_cursor: QTextCursor | None = None
        self._online = True
        self._streaming = False

    def set_available(self, online: bool) -> None:
        """Offline: the question stays in the input field, only sending is paused."""
        self._online = online
        self._sync_buttons()

    def _sync_buttons(self) -> None:
        can_send = self._online and not self._streaming
        self.send_button.setEnabled(can_send)
        self.hint_button.setEnabled(can_send)
        self.stop_button.setEnabled(self._streaming)
        tip = "" if self._online else "Der Lernhelfer macht Pause. Deine Frage bleibt hier stehen."
        self.send_button.setToolTip(tip)
        self.hint_button.setToolTip(tip)

    def _update_counter(self) -> None:
        text = self.input.toPlainText()
        if len(text) > 2000:
            cursor = self.input.textCursor()
            self.input.setPlainText(text[:2000])
            cursor.setPosition(2000)
            self.input.setTextCursor(cursor)
            text = text[:2000]
        self.counter.setText(f"{len(text)} / 2000")

    def _submit(self) -> None:
        text = self.input.toPlainText().strip()
        if not text or not self.send_button.isEnabled():
            return
        self.append_message("Du", text, QColor(colors().accent))
        self.input.clear()
        self.message_submitted.emit(text)

    def append_message(self, sender: str, text: str, color: QColor) -> None:
        cursor = self.history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if not self.history.document().isEmpty():
            cursor.insertText("\n\n")
        sender_format = QTextCharFormat()
        sender_format.setForeground(color)
        sender_format.setFontWeight(700)
        cursor.insertText(f"{sender}: ", sender_format)
        cursor.insertText(text)
        self.history.setTextCursor(cursor)
        self.history.ensureCursorVisible()

    def begin_stream(self) -> None:
        self._streaming = True
        self._sync_buttons()
        cursor = self.history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if not self.history.document().isEmpty():
            cursor.insertText("\n\n")
        teacher_format = QTextCharFormat()
        teacher_format.setForeground(QColor(colors().success))
        teacher_format.setFontWeight(700)
        cursor.insertText("Lernhelfer: ", teacher_format)
        self._stream_cursor = cursor

    def append_stream_chunk(self, text: str) -> None:
        if self._stream_cursor is None:
            self.begin_stream()
        assert self._stream_cursor is not None
        self._stream_cursor.insertText(text)
        self.history.setTextCursor(self._stream_cursor)
        self.history.ensureCursorVisible()

    def finish_stream(self, response: LearningResponse) -> None:
        if response.code_changes:
            LOG.warning("Ignored forbidden code_changes in learning response")
        if self._stream_cursor is None:
            self.append_message("Lernhelfer", response.message, QColor(colors().success))
        self._stream_cursor = None
        self._streaming = False
        self._sync_buttons()
        self.hint_progress.setValue(response.hint_level)

    def show_error(self, message: str) -> None:
        self.append_message("Hinweis", message, QColor(colors().danger))
        self._stream_cursor = None
        self._streaming = False
        self._sync_buttons()

    def set_context_description(self, filename: str, start: int, end: int) -> None:
        self.context_label.setText(f"Ich zeige dem Lernhelfer: {filename}, Zeilen {start}–{end}.")
