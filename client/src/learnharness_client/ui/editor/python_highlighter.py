"""Python syntax highlighter."""

from __future__ import annotations

import keyword

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QTextDocument

from ..theme import code_color

_IN_DOUBLE_TRIPLE = 1
_IN_SINGLE_TRIPLE = 2
_DELIMITERS = {_IN_DOUBLE_TRIPLE: '"""', _IN_SINGLE_TRIPLE: "'''"}


def _format(color: QColor, *, bold: bool = False, italic: bool = False) -> QTextCharFormat:
    result = QTextCharFormat()
    result.setForeground(color)
    if bold:
        result.setFontWeight(QFont.Weight.Bold)
    result.setFontItalic(italic)
    return result


def _utf16(text: str, index: int) -> int:
    """Qt counts UTF-16 units, so an emoji in a string counts as two."""
    return index if text.isascii() else len(text[:index].encode("utf-16-le")) // 2


def _find_close(text: str, start: int, delimiter: str) -> int:
    """Index just after the closing delimiter, or -1. Backslashes escape one character."""
    index = start
    while index < len(text):
        if text[index] == "\\":
            index += 2
        elif text.startswith(delimiter, index):
            return index + len(delimiter)
        else:
            index += 1
    return -1


class PythonHighlighter(QSyntaxHighlighter):
    KEYWORDS = tuple(keyword.kwlist)
    BUILTINS = (
        "abs",
        "bool",
        "dict",
        "enumerate",
        "float",
        "input",
        "int",
        "len",
        "list",
        "max",
        "min",
        "open",
        "print",
        "range",
        "round",
        "set",
        "sorted",
        "str",
        "sum",
        "tuple",
        "type",
        "zip",
        "self",
        "cls",
    )

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)
        self.rules: list[tuple[QRegularExpression, QTextCharFormat]] = [
            (
                QRegularExpression(r"\b(?:" + "|".join(self.KEYWORDS) + r")\b"),
                _format(code_color("keyword"), bold=True),
            ),
            (
                QRegularExpression(r"\b(?:" + "|".join(self.BUILTINS) + r")\b"),
                _format(code_color("type")),
            ),
            (
                QRegularExpression(r"\b(?:0[xX][0-9A-Fa-f_]+|\d[\d_]*(?:\.\d+)?)\b"),
                _format(code_color("number")),
            ),
            (
                QRegularExpression(r"^\s*\K@[A-Za-z_][\w.]*"),
                _format(code_color("annotation"), bold=True),
            ),
        ]
        self.string_format = _format(code_color("string"))
        self.comment_format = _format(code_color("comment"), italic=True)

    def _paint(self, text: str, start: int, end: int, text_format: QTextCharFormat) -> None:
        first = _utf16(text, start)
        self.setFormat(first, _utf16(text, end) - first, text_format)

    def highlightBlock(self, text: str) -> None:  # noqa: N802 - Qt API
        for pattern, text_format in self.rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), text_format)

        self.setCurrentBlockState(0)
        index = 0
        state = self.previousBlockState()
        if state in _DELIMITERS:
            end = _find_close(text, 0, _DELIMITERS[state])
            if end < 0:
                self._paint(text, 0, len(text), self.string_format)
                self.setCurrentBlockState(state)
                return
            self._paint(text, 0, end, self.string_format)
            index = end

        # One pass from the left, so a "#" in a string is no comment and a quote in a
        # comment starts no string.
        while index < len(text):
            character = text[index]
            if character == "#":
                self._paint(text, index, len(text), self.comment_format)
                return
            if character not in "\"'":
                index += 1
                continue
            triple = text.startswith(character * 3, index)
            delimiter = character * 3 if triple else character
            end = _find_close(text, index + len(delimiter), delimiter)
            if end < 0:
                self._paint(text, index, len(text), self.string_format)
                if triple:
                    self.setCurrentBlockState(
                        _IN_DOUBLE_TRIPLE if character == '"' else _IN_SINGLE_TRIPLE
                    )
                return
            self._paint(text, index, end, self.string_format)
            index = end
