"""Godot 4 GDScript syntax highlighter."""

from __future__ import annotations

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QTextDocument

from ..theme import CODE_COLORS


def _format(color: QColor, *, bold: bool = False, italic: bool = False) -> QTextCharFormat:
    result = QTextCharFormat()
    result.setForeground(color)
    if bold:
        result.setFontWeight(QFont.Weight.Bold)
    result.setFontItalic(italic)
    return result


class GDScriptHighlighter(QSyntaxHighlighter):
    KEYWORDS = [
        "and",
        "as",
        "assert",
        "await",
        "break",
        "breakpoint",
        "class",
        "class_name",
        "const",
        "continue",
        "elif",
        "else",
        "enum",
        "extends",
        "for",
        "func",
        "if",
        "in",
        "is",
        "match",
        "namespace",
        "not",
        "or",
        "pass",
        "preload",
        "return",
        "self",
        "signal",
        "static",
        "super",
        "trait",
        "var",
        "void",
        "while",
        "when",
        "yield",
    ]
    TYPES = [
        "bool",
        "int",
        "float",
        "String",
        "StringName",
        "Array",
        "Dictionary",
        "Vector2",
        "Vector2i",
        "Vector3",
        "Vector3i",
        "Vector4",
        "Color",
        "Node",
        "Node2D",
        "Node3D",
        "Control",
        "CharacterBody2D",
        "CharacterBody3D",
        "RigidBody2D",
        "Area2D",
        "Sprite2D",
        "AnimatedSprite2D",
        "Timer",
        "InputEvent",
        "Resource",
        "PackedScene",
        "Callable",
    ]

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)
        self.rules: list[tuple[QRegularExpression, QTextCharFormat]] = []
        keyword_format = _format(CODE_COLORS["keyword"], bold=True)
        type_format = _format(CODE_COLORS["type"])
        self.rules.append(
            (QRegularExpression(r"\b(?:" + "|".join(self.KEYWORDS) + r")\b"), keyword_format)
        )
        self.rules.append(
            (QRegularExpression(r"\b(?:" + "|".join(self.TYPES) + r")\b"), type_format)
        )
        self.rules.extend(
            [
                (
                    QRegularExpression(r"\b(?:0x[0-9A-Fa-f]+|\d+(?:\.\d+)?)\b"),
                    _format(CODE_COLORS["number"]),
                ),
                (
                    QRegularExpression(r"@[A-Za-z_]\w*"),
                    _format(CODE_COLORS["annotation"], bold=True),
                ),
                (QRegularExpression(r"(?:\$|%)[A-Za-z0-9_./]+"), _format(CODE_COLORS["node_path"])),
                (QRegularExpression(r'"(?:\\.|[^"\\])*"'), _format(CODE_COLORS["string"])),
                (QRegularExpression(r"'(?:\\.|[^'\\])*'"), _format(CODE_COLORS["string"])),
                (QRegularExpression(r"#.*$"), _format(CODE_COLORS["comment"], italic=True)),
            ]
        )
        self.triple = QRegularExpression(r'"""')
        self.triple_format = _format(CODE_COLORS["string"])

    def highlightBlock(self, text: str) -> None:  # noqa: N802 - Qt API
        for pattern, text_format in self.rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), text_format)

        self.setCurrentBlockState(0)
        start = 0
        if self.previousBlockState() == 1:
            start = 0
        else:
            match = self.triple.match(text)
            start = match.capturedStart() if match.hasMatch() else -1
        while start >= 0:
            closing = self.triple.match(text, start + 3)
            if closing.hasMatch():
                length = closing.capturedEnd() - start
                self.setFormat(start, length, self.triple_format)
                next_match = self.triple.match(text, closing.capturedEnd())
                start = next_match.capturedStart() if next_match.hasMatch() else -1
            else:
                self.setCurrentBlockState(1)
                self.setFormat(start, len(text) - start, self.triple_format)
                break
