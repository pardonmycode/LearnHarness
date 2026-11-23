"""Tutor conversation without any apply-to-editor action."""

from __future__ import annotations

import logging

from learnharness_protocol import LearningResponse
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QKeyEvent, QTextBlockFormat, QTextCharFormat, QTextCursor
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

from learnharness_client import design

from ...texts import T
from ..markdown import insert_markdown
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
        layout.setContentsMargins(*design.PANEL_MARGINS)
        layout.setSpacing(design.PANEL_SPACING_TIGHT)
        heading = QLabel(T.TUTOR_NAME)
        heading.setProperty("role", "heading")
        layout.addWidget(heading)
        self.context_label = QLabel(T.TUTOR_CONTEXT_DEFAULT)
        self.context_label.setWordWrap(True)
        self.context_label.setProperty("role", "small")
        self.history = QTextBrowser()
        self.history.setOpenExternalLinks(False)
        self.history.setOpenLinks(False)
        self.history.setAccessibleName(T.TUTOR_HISTORY_A11Y)
        self.input = MessageInput()
        self.input.setPlaceholderText(T.TUTOR_INPUT_PLACEHOLDER)
        self.input.setMaximumHeight(design.TUTOR_INPUT_MAX_HEIGHT)
        self.input.setAccessibleName(T.TUTOR_INPUT_A11Y)
        self.counter = QLabel("0 / 2000")
        self.hint_progress = QProgressBar()
        self.hint_progress.setRange(0, 4)
        self.hint_progress.setValue(0)
        self.hint_progress.setFormat(T.TUTOR_HINT_PROGRESS)
        buttons = QHBoxLayout()
        self.send_button = QPushButton(T.TUTOR_SEND)
        self.send_button.setProperty("primary", "true")
        self.hint_button = QPushButton(T.TUTOR_NEXT_HINT)
        self.stop_button = QPushButton(T.TUTOR_STOP)
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
        self._stream_start = 0
        self._stream_text = ""
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
        tip = "" if self._online else T.TUTOR_OFFLINE_TIP
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
        self.append_message(T.CHILD_NAME, text, QColor(colors().accent), markdown=False)
        self.input.clear()
        self.message_submitted.emit(text)

    def ask(self, text: str) -> None:
        """Sends a question for the child, for example a hint request."""
        if not self.send_button.isEnabled():
            return
        self.append_message(T.CHILD_NAME, text, QColor(colors().accent), markdown=False)
        self.message_submitted.emit(text)

    def _begin_message(self, sender: str, color: QColor) -> QTextCursor:
        cursor = self.history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if not self.history.document().isEmpty():
            cursor.insertBlock(QTextBlockFormat())
            cursor.insertBlock(QTextBlockFormat())
        sender_format = QTextCharFormat()
        sender_format.setForeground(color)
        sender_format.setFontWeight(700)
        cursor.insertText(sender, sender_format)
        cursor.insertBlock(QTextBlockFormat(), QTextCharFormat())
        return cursor

    def append_message(
        self, sender: str, text: str, color: QColor, *, markdown: bool = True
    ) -> None:
        cursor = self._begin_message(sender, color)
        if markdown:
            insert_markdown(cursor, text)
        else:
            # The child's own text is shown exactly as typed.
            cursor.insertText(text)
        self.history.setTextCursor(cursor)
        self.history.ensureCursorVisible()

    def begin_stream(self) -> None:
        self._streaming = True
        self._sync_buttons()
        cursor = self._begin_message(T.TUTOR_NAME, QColor(colors().success))
        self._stream_start = cursor.position()
        self._stream_text = ""
        self._stream_cursor = cursor

    def append_stream_chunk(self, text: str) -> None:
        if self._stream_cursor is None:
            self.begin_stream()
        assert self._stream_cursor is not None
        self._stream_text += text
        # Re-render the growing answer so Markdown (lists, code) appears while streaming.
        cursor = self._stream_cursor
        cursor.setPosition(self._stream_start)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        insert_markdown(cursor, self._stream_text)
        self.history.setTextCursor(cursor)
        self.history.ensureCursorVisible()

    def finish_stream(self, response: LearningResponse) -> None:
        if response.code_changes:
            LOG.warning("Ignored forbidden code_changes in learning response")
        if self._stream_cursor is None:
            self.append_message(T.TUTOR_NAME, response.message, QColor(colors().success))
        self._stream_cursor = None
        self._streaming = False
        self._sync_buttons()
        self.hint_progress.setValue(response.hint_level)

    def show_error(self, message: str) -> None:
        self.append_message(T.NOTICE_NAME, message, QColor(colors().danger), markdown=False)
        self._stream_cursor = None
        self._streaming = False
        self._sync_buttons()

    def set_context_description(
        self, filename: str, start: int, end: int, *, with_idea: bool = False
    ) -> None:
        template = T.TUTOR_CONTEXT_WITH_IDEA if with_idea else T.TUTOR_CONTEXT
        self.context_label.setText(template.format(file=filename, start=start, end=end))
