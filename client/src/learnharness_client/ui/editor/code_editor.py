"""QPlainTextEdit with line numbers and GDScript-friendly editing."""

from __future__ import annotations

from PyQt6.QtCore import QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QKeyEvent,
    QPainter,
    QPaintEvent,
    QTextCursor,
    QTextFormat,
    QWheelEvent,
)
from PyQt6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

from .gdscript_highlighter import GDScriptHighlighter


class LineNumberArea(QWidget):
    def __init__(self, editor: CodeEditor) -> None:
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt API
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 - Qt API
        self.editor.paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    cursor_location_changed = pyqtSignal(int, int)
    font_size_changed = pyqtSignal(int)

    def __init__(self, parent=None, *, font_size: int = 14) -> None:
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.error_lines: set[int] = set()
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(font_size)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setAcceptDrops(False)
        self.highlighter = GDScriptHighlighter(self.document())
        self.blockCountChanged.connect(self._update_margin)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._cursor_changed)
        self._update_margin()
        self._cursor_changed()

    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        return 14 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_margin(self, _count: int = 0) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_margin()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        contents = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(contents.left(), contents.top(), self.line_number_area_width(), contents.height())
        )

    def paint_line_numbers(self, event: QPaintEvent) -> None:
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#f1f5f9"))
        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                line_number = number + 1
                painter.setPen(
                    QColor("#b91c1c") if line_number in self.error_lines else QColor("#64748b")
                )
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 5,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(line_number),
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            number += 1

    def _cursor_changed(self) -> None:
        cursor = self.textCursor()
        self.cursor_location_changed.emit(cursor.blockNumber() + 1, cursor.positionInBlock() + 1)
        self._update_extra_selections()

    def _update_extra_selections(self) -> None:
        selections: list[QTextEdit.ExtraSelection] = []
        current = QTextEdit.ExtraSelection()
        current.format.setBackground(QColor("#eff6ff"))
        current.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        current.cursor = self.textCursor()
        current.cursor.clearSelection()
        selections.append(current)
        for line in self.error_lines:
            block = self.document().findBlockByNumber(line - 1)
            if not block.isValid():
                continue
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#fee2e2"))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = QTextCursor(block)
            selections.append(selection)
        self.setExtraSelections(selections)
        self.line_number_area.update()

    def set_error_lines(self, lines: list[int]) -> None:
        self.error_lines = {line for line in lines if line > 0}
        self._update_extra_selections()

    def goto_line(self, line: int) -> None:
        block = self.document().findBlockByNumber(max(0, line - 1))
        if block.isValid():
            self.setTextCursor(QTextCursor(block))
            self.centerCursor()
            self.setFocus()

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
            indentation = current_line[: len(current_line) - len(current_line.lstrip("\t"))]
            if current_line.rstrip().endswith(":"):
                indentation += "\t"
            super().keyPressEvent(event)
            self.insertPlainText(indentation)
            return
        super().keyPressEvent(event)

    def _indent_selection(self, outdent: bool) -> None:
        cursor = self.textCursor()
        if not cursor.hasSelection():
            if outdent:
                cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                cursor.movePosition(
                    QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1
                )
                if cursor.selectedText() == "\t":
                    cursor.removeSelectedText()
            else:
                cursor.insertText("\t")
            return
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.beginEditBlock()
        while cursor.position() <= end:
            if outdent:
                cursor.movePosition(
                    QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1
                )
                if cursor.selectedText() == "\t":
                    cursor.removeSelectedText()
                    end -= 1
                else:
                    cursor.clearSelection()
            else:
                cursor.insertText("\t")
                end += 1
            if not cursor.movePosition(QTextCursor.MoveOperation.NextBlock):
                break
        cursor.endEditBlock()

    def _change_font_size(self, delta: int) -> None:
        size = max(11, min(28, self.font().pointSize() + delta))
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self._update_margin()
        self.font_size_changed.emit(size)
