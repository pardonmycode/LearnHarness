"""Compact find/replace bar for the active code editor."""

from __future__ import annotations

from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from learnharness_client import design

from ...texts import T
from .code_editor import CodeEditor


class FindBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.editor: CodeEditor | None = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(*design.FIND_BAR_MARGINS)
        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText(T.FIND_PLACEHOLDER)
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText(T.REPLACE_PLACEHOLDER)
        next_button = QPushButton(T.FIND_NEXT)
        replace_button = QPushButton(T.REPLACE_BUTTON)
        close_button = QPushButton(T.CLOSE)
        layout.addWidget(QLabel(T.FIND_LABEL))
        layout.addWidget(self.find_edit)
        layout.addWidget(self.replace_edit)
        layout.addWidget(next_button)
        layout.addWidget(replace_button)
        layout.addWidget(close_button)
        next_button.clicked.connect(self.find_next)
        replace_button.clicked.connect(self.replace_current)
        close_button.clicked.connect(self.hide)
        self.find_edit.returnPressed.connect(self.find_next)
        self.hide()

    def attach(self, editor: CodeEditor | None) -> None:
        self.editor = editor

    def open_find(self, with_replace: bool = False) -> None:
        self.replace_edit.setVisible(with_replace)
        self.show()
        self.find_edit.setFocus()
        self.find_edit.selectAll()

    def find_next(self) -> None:
        if not self.editor or not self.find_edit.text():
            return
        if not self.editor.find(self.find_edit.text()):
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)
            self.editor.find(self.find_edit.text())

    def replace_current(self) -> None:
        if not self.editor:
            return
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_edit.text())
        self.find_next()
