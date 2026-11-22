"""Side-by-side view of what the LearnAgent changed in a file."""

from __future__ import annotations

import difflib
from dataclasses import dataclass

from PyQt6.QtGui import QColor, QTextBlockFormat, QTextCursor
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
)

from ...texts import T
from ..editor.highlighters import highlighter_for_file
from ..theme import colors, monospace_font


@dataclass(frozen=True, slots=True)
class LineChanges:
    removed: frozenset[int]  # 0-based line numbers in the old text
    added: frozenset[int]  # 0-based line numbers in the new text


def line_changes(old: str, new: str) -> LineChanges:
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    removed: set[int] = set()
    added: set[int] = set()
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if tag in ("replace", "delete"):
            removed.update(range(old_start, old_end))
        if tag in ("replace", "insert"):
            added.update(range(new_start, new_end))
    return LineChanges(frozenset(removed), frozenset(added))


def _code_pane(text: str, accessible_name: str, file_name: str) -> QPlainTextEdit:
    view = QPlainTextEdit(text)
    view.setObjectName("codeView")
    view.setReadOnly(True)
    view.setFont(monospace_font())
    view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    view.setAccessibleName(accessible_name)
    view._highlighter = highlighter_for_file(  # type: ignore[attr-defined]
        view.document(), file_name
    )
    return view


def _mark_lines(view: QPlainTextEdit, lines: frozenset[int], color: str) -> None:
    block_format = QTextBlockFormat()
    block_format.setBackground(QColor(color))
    document = view.document()
    assert document is not None
    for line in lines:
        block = document.findBlockByNumber(line)
        if block.isValid():
            QTextCursor(block).setBlockFormat(block_format)


class ChangesDialog(QDialog):
    def __init__(self, file_name: str, old: str, new: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(T.CHANGES_TITLE.format(file=file_name))
        self.resize(1100, 620)
        self.changes = line_changes(old, new)
        layout = QVBoxLayout(self)
        intro = QLabel(T.CHANGES_INTRO)
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")
        summary = QLabel(
            T.CHANGES_SUMMARY.format(
                added=len(self.changes.added), removed=len(self.changes.removed)
            )
        )
        summary.setProperty("role", "subheading")
        layout.addWidget(intro)
        layout.addWidget(summary)

        grid = QGridLayout()
        old_title = QLabel(T.CHANGES_OLD)
        old_title.setProperty("role", "section")
        new_title = QLabel(T.CHANGES_NEW)
        new_title.setProperty("role", "section")
        self.old_view = _code_pane(old or T.CHANGES_NEW_FILE, T.CHANGES_OLD_A11Y, file_name)
        self.new_view = _code_pane(new, T.CHANGES_NEW_A11Y, file_name)
        c = colors()
        if old:
            _mark_lines(self.old_view, self.changes.removed, c.danger_bg)
        _mark_lines(self.new_view, self.changes.added, c.success_bg)
        grid.addWidget(old_title, 0, 0)
        grid.addWidget(new_title, 0, 1)
        grid.addWidget(self.old_view, 1, 0)
        grid.addWidget(self.new_view, 1, 1)
        layout.addLayout(grid, 1)
        self._sync_scrolling()

        buttons = QDialogButtonBox()
        close = buttons.addButton(T.CHANGES_CLOSE, QDialogButtonBox.ButtonRole.AcceptRole)
        assert close is not None
        close.setProperty("primary", "true")
        close.setDefault(True)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _sync_scrolling(self) -> None:
        old_bar = self.old_view.verticalScrollBar()
        new_bar = self.new_view.verticalScrollBar()
        if old_bar is None or new_bar is None:
            return
        old_bar.valueChanged.connect(new_bar.setValue)
        new_bar.valueChanged.connect(old_bar.setValue)
