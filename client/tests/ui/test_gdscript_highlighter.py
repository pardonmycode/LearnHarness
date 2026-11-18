"""The highlighter colors example GDScript lines in the expected ranges."""

from __future__ import annotations

import pytest
from PyQt6.QtGui import QColor, QTextDocument

from learnharness_client.ui.editor.gdscript_highlighter import GDScriptHighlighter
from learnharness_client.ui.theme import code_color


def _colors_by_char(code: str) -> list[list[str | None]]:
    """For each line, the foreground color name of every character (None = unformatted)."""
    document = QTextDocument()
    highlighter = GDScriptHighlighter(document)
    document.setPlainText(code)
    highlighter.rehighlight()
    result: list[list[str | None]] = []
    block = document.begin()
    while block.isValid():
        chars: list[str | None] = [None] * len(block.text())
        layout = block.layout()
        assert layout is not None
        for fmt_range in layout.formats():
            color = fmt_range.format.foreground().color().name()
            for index in range(fmt_range.start, fmt_range.start + fmt_range.length):
                if index < len(chars):
                    chars[index] = color
        result.append(chars)
        block = block.next()
    return result


def _span(line: list[str | None], text: str, word: str) -> set[str | None]:
    start = text.index(word)
    return set(line[start : start + len(word)])


def _name(kind: str) -> str:
    return QColor(code_color(kind)).name()


@pytest.mark.parametrize(
    ("line", "word", "kind"),
    [
        ("func _ready():", "func", "keyword"),
        ("extends CharacterBody2D", "extends", "keyword"),
        ("extends CharacterBody2D", "CharacterBody2D", "type"),
        ("var speed: float = 200.5", "float", "type"),
        ("var speed: float = 200.5", "200.5", "number"),
        ("var mask = 0xFF", "0xFF", "number"),
        ('print("Hallo Welt")', '"Hallo Welt"', "string"),
        ("print('einfach')", "'einfach'", "string"),
        ("@export var hp = 3", "@export", "annotation"),
        ("var hp = 3  # Leben", "# Leben", "comment"),
        ("$Sprite2D.visible = false", "$Sprite2D", "node_path"),
    ],
)
def test_example_lines_get_expected_colors(line: str, word: str, kind: str) -> None:
    chars = _colors_by_char(line)[0]
    assert _span(chars, line, word) == {_name(kind)}


def test_keywords_inside_strings_and_comments_are_not_keywords() -> None:
    line = 'print("func if var")  # return self'
    chars = _colors_by_char(line)[0]
    assert _span(chars, line, '"func if var"') == {_name("string")}
    assert _span(chars, line, "# return self") == {_name("comment")}


def test_identifiers_stay_unformatted() -> None:
    line = "velocity = direction"
    chars = _colors_by_char(line)[0]
    assert set(chars) == {None}


def test_keyword_needs_word_boundary() -> None:
    line = "var function_name = 1"
    chars = _colors_by_char(line)[0]
    assert _span(chars, line, "function_name") == {None}


def test_multiline_docstring_spans_blocks() -> None:
    code = 'var a = """erste\nzweite Zeile\nende""" + b'
    lines = _colors_by_char(code)
    string = _name("string")
    assert set(lines[1]) == {string}
    assert set(lines[2][: len('ende"""')]) == {string}
    assert lines[2][-1] is None
