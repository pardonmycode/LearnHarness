"""Text area that behaves like a console: only the current input line can be edited."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QKeySequence, QTextCursor
from PyQt6.QtWidgets import QPlainTextEdit

from ...texts import T
from ..theme import monospace_font

MAX_LINES = 2000
MAX_CHARACTERS = 200_000
_MOVE = QTextCursor.MoveMode
_NAVIGATION = {
    Qt.Key.Key_Left,
    Qt.Key.Key_Right,
    Qt.Key.Key_PageUp,
    Qt.Key.Key_PageDown,
    Qt.Key.Key_End,
    Qt.Key.Key_Shift,
    Qt.Key.Key_Control,
    Qt.Key.Key_Meta,
    Qt.Key.Key_Alt,
}


class TerminalConsole(QPlainTextEdit):
    line_entered = pyqtSignal(str)
    interrupt_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("codeView")
        self.setFont(monospace_font(12))
        self.setMaximumBlockCount(MAX_LINES)
        self.setUndoRedoEnabled(False)
        self.setAcceptDrops(False)
        self.setTabChangesFocus(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setAccessibleName(T.TERMINAL_A11Y)
        self._history: list[str] = []
        self._history_index = 0
        self._input_start = QTextCursor(self.document())
        # Typing right at the start of the input must not push the boundary forward.
        self._input_start.setKeepPositionOnInsert(True)

    def input_text(self) -> str:
        cursor = QTextCursor(self.document())
        cursor.setPosition(self._input_start.position())
        cursor.movePosition(QTextCursor.MoveOperation.End, _MOVE.KeepAnchor)
        return cursor.selectedText()

    def reset(self) -> None:
        self.clear()
        self._input_start = QTextCursor(self.document())
        self._input_start.setKeepPositionOnInsert(True)

    def write(self, text: str) -> None:
        """Adds output before the input line, so typing is never mixed into it."""
        bar = self.verticalScrollBar()
        follow = bar is None or bar.value() >= bar.maximum() - 2
        cursor = QTextCursor(self.document())
        cursor.setPosition(self._input_start.position())
        cursor.insertText(text)
        self._input_start.setPosition(cursor.position())
        excess = self.document().characterCount() - MAX_CHARACTERS
        if excess > 0:
            # One endless line never reaches the line limit.
            cursor.setPosition(0)
            cursor.setPosition(excess + MAX_CHARACTERS // 2, _MOVE.KeepAnchor)
            cursor.removeSelectedText()
        if follow and bar is not None:
            bar.setValue(bar.maximum())

    def at_line_start(self) -> bool:
        position = self._input_start.position()
        return position == 0 or self.document().characterAt(position - 1) == " "

    def focus_input(self) -> None:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 - Qt API
        key = event.key()
        control = event.modifiers() & (
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier
        )
        if key == Qt.Key.Key_C and control:
            if self.textCursor().hasSelection():
                self.copy()
            else:
                self.interrupt_requested.emit()
            return
        if event.matches(QKeySequence.StandardKey.SelectAll):
            super().keyPressEvent(event)
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._submit()
        elif key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            self._browse_history(-1 if key == Qt.Key.Key_Up else 1)
        elif key == Qt.Key.Key_Home:
            self._go_to_input_start(event)
        elif key == Qt.Key.Key_Backspace:
            self._backspace()
        elif key == Qt.Key.Key_Left and self._at_boundary():
            return
        else:
            if key not in _NAVIGATION:
                self._keep_cursor_in_input()
            super().keyPressEvent(event)

    def insertFromMimeData(self, source) -> None:  # noqa: N802 - Qt API
        if source.hasText():
            self._keep_cursor_in_input()
            self.insertPlainText(" ".join(source.text().split("\n")))

    def _at_boundary(self) -> bool:
        cursor = self.textCursor()
        return not cursor.hasSelection() and cursor.position() <= self._input_start.position()

    def _keep_cursor_in_input(self) -> None:
        cursor = self.textCursor()
        if cursor.selectionStart() < self._input_start.position():
            cursor.clearSelection()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.setTextCursor(cursor)

    def _backspace(self) -> None:
        self._keep_cursor_in_input()
        if self._at_boundary():
            return
        cursor = self.textCursor()
        cursor.deletePreviousChar()
        self.setTextCursor(cursor)

    def _go_to_input_start(self, event: QKeyEvent) -> None:
        cursor = self.textCursor()
        keep = event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        cursor.setPosition(
            self._input_start.position(), _MOVE.KeepAnchor if keep else _MOVE.MoveAnchor
        )
        self.setTextCursor(cursor)

    def _submit(self) -> None:
        text = self.input_text()
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText("\n")
        self._input_start.setPosition(cursor.position())
        self.setTextCursor(cursor)
        if text.strip() and (not self._history or self._history[-1] != text):
            self._history.append(text)
        self._history_index = len(self._history)
        self.line_entered.emit(text)

    def _browse_history(self, step: int) -> None:
        if not self._history:
            return
        self._history_index = max(0, min(len(self._history), self._history_index + step))
        known = self._history_index < len(self._history)
        text = self._history[self._history_index] if known else ""
        cursor = QTextCursor(self.document())
        cursor.setPosition(self._input_start.position())
        cursor.movePosition(QTextCursor.MoveOperation.End, _MOVE.KeepAnchor)
        cursor.insertText(text)
        self.setTextCursor(cursor)
