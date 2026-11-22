"""Choose the syntax highlighter for a language or file."""

from __future__ import annotations

from pathlib import PurePath

from PyQt6.QtGui import QSyntaxHighlighter, QTextDocument

from .gdscript_highlighter import GDScriptHighlighter
from .python_highlighter import PythonHighlighter


def create_highlighter(document: QTextDocument, language: str) -> QSyntaxHighlighter:
    if language == "python":
        return PythonHighlighter(document)
    return GDScriptHighlighter(document)


def highlighter_for_file(document: QTextDocument, file_name: str) -> QSyntaxHighlighter:
    is_python = PurePath(file_name).suffix.casefold() == ".py"
    return create_highlighter(document, "python" if is_python else "gdscript")
