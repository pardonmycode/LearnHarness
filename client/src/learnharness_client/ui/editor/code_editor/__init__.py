"""QPlainTextEdit with line numbers and editing rules for GDScript and Python."""

from __future__ import annotations

from PyQt6.QtCore import QRect, Qt, pyqtSignal
from PyQt6.QtGui import QContextMenuEvent, QKeyEvent, QTextCursor, QWheelEvent
from PyQt6.QtWidgets import QPlainTextEdit

from ....texts import T
from ...theme import monospace_font
from ..highlighters import create_highlighter
from .gutter import EditorGutter, LineNumberArea
from .indentation import EditorIndentation
from .selections import EditorSelections

__all__ = ["CodeEditor", "LineNumberArea"]


class CodeEditor(EditorGutter, EditorSelections, EditorIndentation, QPlainTextEdit):
    explain_requested = pyqtSignal()
    cursor_location_changed = pyqtSignal(int, int)
    font_size_changed = pyqtSignal(int)

    def __init__(self, parent=None, *, font_size: int = 14, language: str = "gdscript") -> None:
        super().__init__(parent)
        self.language = language
        # GDScript uses tabs; Python uses four spaces unless the file already uses tabs.
        self.indent_unit = "    " if language == "python" else "\t"
        self.line_number_area = LineNumberArea(self)
        self.error_lines: set[int] = set()
        self.setObjectName("codeEditor")
        self.setFont(monospace_font(font_size))
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setAcceptDrops(False)
        self.highlighter = create_highlighter(self.document(), language)
        self.blockCountChanged.connect(self._update_margin)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._cursor_changed)
        self._update_margin()
        self._cursor_changed()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        contents = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(contents.left(), contents.top(), self.line_number_area_width(), contents.height())
        )

    def replace_all_text(self, text: str) -> None:
        """Replace the whole content as one undoable step (Strg+Z restores the old code)."""
        cursor = QTextCursor(self.document())
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.insertText(text)
        cursor.endEditBlock()

    def goto_line(self, line: int) -> None:
        block = self.document().findBlockByNumber(max(0, line - 1))
        if block.isValid():
            self.setTextCursor(QTextCursor(block))
            self.centerCursor()
            self.setFocus()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:  # noqa: N802 - Qt API
        menu = self.createStandardContextMenu()
        if menu is None:
            return
        explain = menu.addAction(T.EXPLAIN_CONTEXT_ACTION)
        first = menu.actions()[0]
        if explain is not None:
            menu.insertAction(first, explain)
            menu.insertSeparator(first)
            explain.triggered.connect(self.explain_requested)
        menu.exec(event.globalPos())
        menu.deleteLater()

    def selected_or_nearby_text(self, radius: int = 7) -> tuple[str, int]:
        cursor = self.textCursor()
        if cursor.hasSelection():
            start_cursor = QTextCursor(self.document())
            start_cursor.setPosition(cursor.selectionStart())
            return cursor.selectedText().replace("\u2029", "\n"), start_cursor.blockNumber() + 1
        line = cursor.blockNumber()
        start = max(0, line - radius)
        end = min(self.blockCount() - 1, line + radius)
        lines = self.toPlainText().splitlines()
        return "\n".join(lines[start : end + 1]), start + 1

    def insertFromMimeData(self, source) -> None:  # noqa: N802 - Qt API
        if source.hasText():
            self.insertPlainText(source.text())

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802 - Qt API
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._change_font_size(1 if event.angleDelta().y() > 0 else -1)
            event.accept()
            return
        super().wheelEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 - Qt API
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
                self._change_font_size(1)
                return
            if event.key() == Qt.Key.Key_Minus:
                self._change_font_size(-1)
                return
        if event.key() == Qt.Key.Key_Tab and not event.modifiers():
            self._indent_selection(False)
            return
        if event.key() == Qt.Key.Key_Backtab:
            self._indent_selection(True)
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor = self.textCursor()
            current_line = cursor.block().text()
            blanks = " \t" if self.language == "python" else "\t"
            indentation = current_line[: len(current_line) - len(current_line.lstrip(blanks))]
            if current_line.rstrip().endswith(":"):
                indentation += self.indent_unit
            super().keyPressEvent(event)
            self.insertPlainText(indentation)
            return
        super().keyPressEvent(event)

    def _change_font_size(self, delta: int) -> None:
        size = max(11, min(28, self.font().pointSize() + delta))
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self._update_margin()
        self.font_size_changed.emit(size)
