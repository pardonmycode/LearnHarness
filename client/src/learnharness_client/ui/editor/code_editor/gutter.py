"""Line numbers beside the code."""

from __future__ import annotations

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QColor, QPainter, QPaintEvent
from PyQt6.QtWidgets import QPlainTextEdit, QWidget

from ...theme import colors


class LineNumberArea(QWidget):
    def __init__(self, editor: QPlainTextEdit) -> None:
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt API
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 - Qt API
        self.editor.paint_line_numbers(event)


class EditorGutter:
    """Paints the line number area."""

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
