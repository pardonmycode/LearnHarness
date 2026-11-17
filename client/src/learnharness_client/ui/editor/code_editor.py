"""QPlainTextEdit with line numbers and GDScript-friendly editing."""

from __future__ import annotations

from PyQt6.QtCore import QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QKeyEvent,
    QPainter,
    QPaintEvent,
    QTextCursor,
    QTextFormat,
    QWheelEvent,
)
from PyQt6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

from ..theme import colors, monospace_font
from .gdscript_highlighter import GDScriptHighlighter

_BRACKETS = {"(": ")", "[": "]", "{": "}"}
_CLOSING = {value: key for key, value in _BRACKETS.items()}


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
        self.setObjectName("codeEditor")
        self.setFont(monospace_font(font_size))
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
        return 30 + self.fontMetrics().horizontalAdvance("9") * max(2, digits)

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
        palette = colors()
        painter = QPainter(self.line_number_area)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(event.rect(), QColor(palette.gutter_bg))
        current_line = self.textCursor().blockNumber() + 1
        line_height = self.fontMetrics().height()
        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                line_number = number + 1
                is_error = line_number in self.error_lines
                if is_error:
                    # Colored dot so errors are not signalled by text color alone.
                    radius = max(3, line_height // 5)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(palette.danger))
                    painter.drawEllipse(8, top + line_height // 2 - radius, radius * 2, radius * 2)
                if is_error:
                    pen = QColor(palette.danger)
                elif line_number == current_line:
                    pen = QColor(palette.text)
                else:
                    pen = QColor(palette.gutter_text)
                painter.setPen(pen)
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 10,
                    line_height,
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
        palette = colors()
        selections: list[QTextEdit.ExtraSelection] = []
        current = QTextEdit.ExtraSelection()
        current.format.setBackground(QColor(palette.current_line))
        current.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        current.cursor = self.textCursor()
        current.cursor.clearSelection()
        selections.append(current)
        for line in self.error_lines:
            block = self.document().findBlockByNumber(line - 1)
            if not block.isValid():
                continue
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(palette.error_line))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = QTextCursor(block)
            selections.append(selection)
        selections.extend(self._bracket_selections())
        self.setExtraSelections(selections)
        self.line_number_area.update()

    def _bracket_selections(self) -> list[QTextEdit.ExtraSelection]:
        text = self.toPlainText()
        position = self.textCursor().position()
        candidates = [position, position - 1]
        for index in candidates:
            if 0 <= index < len(text) and (text[index] in _BRACKETS or text[index] in _CLOSING):
                match = self._matching_bracket(text, index)
                if match is None:
                    return []
                result: list[QTextEdit.ExtraSelection] = []
                for bracket_index in (index, match):
                    selection = QTextEdit.ExtraSelection()
                    selection.format.setBackground(QColor(colors().selection))
                    cursor = QTextCursor(self.document())
                    cursor.setPosition(bracket_index)
                    cursor.movePosition(
                        QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor
                    )
                    selection.cursor = cursor
                    result.append(selection)
                return result
        return []

    @staticmethod
    def _matching_bracket(text: str, index: int, limit: int = 20_000) -> int | None:
        char = text[index]
        if char in _BRACKETS:
            opening, closing, step = char, _BRACKETS[char], 1
        else:
            opening, closing, step = char, _CLOSING[char], -1
        depth = 0
        position = index
        for _ in range(limit):
            if not 0 <= position < len(text):
                return None
            if text[position] == opening:
                depth += 1
            elif text[position] == closing:
                depth -= 1
                if depth == 0:
                    return position
            position += step
        return None

    def replace_all_text(self, text: str) -> None:
        """Replace the whole content as one undoable step (Strg+Z restores the old code)."""
        cursor = QTextCursor(self.document())
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.insertText(text)
        cursor.endEditBlock()

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
