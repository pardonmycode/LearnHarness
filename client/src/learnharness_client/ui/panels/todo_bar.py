"""Bar above all tabs: the to-do the child is working on and how to work on it."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from ...texts import T
from ..theme import set_state


class TodoBar(QFrame):
    learn_requested = pyqtSignal()
    mission_requested = pyqtSignal()
    tutor_requested = pyqtSignal()
    done_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("card", "true")
        self.todo_text: str | None = None
        self.section = QLabel()
        self.section.setProperty("role", "section")
        self.todo = QLabel()
        self.todo.setProperty("role", "subheading")
        self.todo.setWordWrap(True)
        self.question = QLabel(T.TODO_ASK_DONE)
        self.question.setWordWrap(True)
        self.question.setProperty("callout", "success")
        self.question.hide()
        self.learn_button = QPushButton(T.TODO_LEARN)
        self.mission_button = QPushButton(T.TODO_MISSION)
        self.tutor_button = QPushButton(T.TODO_TUTOR)
        self.done_button = QPushButton(T.TODO_DONE)
        self.done_button.setProperty("primary", "true")
        self.learn_button.setToolTip(T.TODO_LEARN_TIP)
        self.mission_button.setToolTip(T.TODO_MISSION_TIP)
        self.tutor_button.setToolTip(T.TODO_TUTOR_TIP)
        self.learn_button.clicked.connect(self.learn_requested)
        self.mission_button.clicked.connect(self.mission_requested)
        self.tutor_button.clicked.connect(self.tutor_requested)
        self.done_button.clicked.connect(self.done_requested)
        self.buttons = [self.learn_button, self.mission_button, self.tutor_button, self.done_button]
        row = QHBoxLayout()
        row.addWidget(self.learn_button)
        row.addWidget(self.mission_button)
        row.addWidget(self.tutor_button)
        row.addStretch(1)
        row.addWidget(self.done_button)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)
        layout.addWidget(self.section)
        layout.addWidget(self.todo)
        layout.addWidget(self.question)
        layout.addLayout(row)
        self.hide()

    def show_todo(self, text: str | None, position: int, total: int) -> None:
        if text != self.todo_text:
            self.question.hide()
        self.todo_text = text
        self.setVisible(total > 0)
        if text is None:
            self.section.setText(T.TODO_ALL_DONE_SECTION)
            self.todo.setText(T.TODO_ALL_DONE)
        else:
            self.section.setText(T.TODO_SECTION.format(current=position, total=total))
            self.todo.setText(text)
        for button in self.buttons:
            button.setVisible(text is not None)

    def ask_if_done(self) -> None:
        if self.todo_text is not None:
            set_state(self.question, callout="success")
            self.question.show()
