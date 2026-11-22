"""Indenting and outdenting for GDScript and Python."""

from __future__ import annotations

from PyQt6.QtGui import QTextCursor


class EditorIndentation:
    """Indentation rules."""

    def adopt_indentation(self, text: str) -> None:
        """Mixing tabs and spaces is an error in Python, so follow what the file uses."""
        if self.language == "python":
            uses_tabs = any(line.startswith("\t") for line in text.splitlines())
            self.indent_unit = "\t" if uses_tabs else "    "

    def _outdent_length(self, line: str) -> int:
        if line.startswith("\t"):
            return 1
        if self.indent_unit == "\t":
            return 0
        prefix = line[: len(self.indent_unit)]
        return len(prefix) - len(prefix.lstrip(" "))

    def _indent_selection(self, outdent: bool) -> None:
        cursor = self.textCursor()
        if not cursor.hasSelection():
            if outdent:
                length = self._outdent_length(cursor.block().text())
                cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                if length:
                    cursor.movePosition(
                        QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, length
                    )
                    cursor.removeSelectedText()
            else:
                cursor.insertText(self.indent_unit)
            return
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.beginEditBlock()
        while cursor.position() <= end:
            if outdent:
                length = self._outdent_length(cursor.block().text())
                if length:
                    cursor.movePosition(
                        QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, length
                    )
                    cursor.removeSelectedText()
                    end -= length
            else:
                cursor.insertText(self.indent_unit)
                end += len(self.indent_unit)
            if not cursor.movePosition(QTextCursor.MoveOperation.NextBlock):
                break
        cursor.endEditBlock()
