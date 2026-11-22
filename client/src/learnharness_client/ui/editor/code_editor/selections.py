"""Current line, error lines and matching brackets."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QTextCursor, QTextFormat
from PyQt6.QtWidgets import QTextEdit

from ...theme import colors

_BRACKETS = {"(": ")", "[": "]", "{": "}"}


_CLOSING = {value: key for key, value in _BRACKETS.items()}


class EditorSelections:
    """Highlights in the text."""

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

    def set_error_lines(self, lines: list[int]) -> None:
        self.error_lines = {line for line in lines if line > 0}
        self._update_extra_selections()
