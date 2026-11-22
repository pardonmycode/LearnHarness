"""Describe the project and build its to-do list together with the learning helper."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from learnharness_client.domain.project_plan import MAX_TODO_LENGTH, ProjectPlan

from ....texts import T
from ..learn_agent_panel import card
from .planning import PanelPlanning
from .rendering import PanelRendering
from .todo_list import PanelTodoList

__all__ = ["ProjectPanel"]


class ProjectPanel(PanelPlanning, PanelTodoList, PanelRendering, QWidget):
    plan_requested = pyqtSignal(str)  # the description or the child's answer
    plan_changed = pyqtSignal(dict)  # JSON-ready state for saving

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.plan = ProjectPlan()
        self._online = True
        self._busy = False
        self._has_project = False

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        heading = QLabel(T.PLAN_HEADING)
        heading.setProperty("role", "heading")
        intro = QLabel(T.PLAN_INTRO)
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")

        idea_card, idea_layout = card(T.PLAN_IDEA_SECTION)
        self.description = QPlainTextEdit()
        self.description.setAccessibleName(T.PLAN_IDEA_A11Y)
        self.description.setPlaceholderText(T.PLAN_IDEA_PLACEHOLDER)
        self.description.setTabChangesFocus(True)
        self.description.setFixedHeight(110)
        self.description.textChanged.connect(self._description_changed)
        self.plan_button = QPushButton(T.PLAN_START)
        self.plan_button.setProperty("primary", "true")
        self.plan_button.clicked.connect(self._request_from_description)
        idea_layout.addWidget(self.description)
        idea_layout.addWidget(self.plan_button, 0, Qt.AlignmentFlag.AlignRight)

        self.message = QLabel()
        self.message.setWordWrap(True)
        self.message.setProperty("callout", "neutral")
        self.message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.message.hide()

        self.helper_card, helper_layout = card(T.PLAN_HELPER_SECTION)
        self.question = QLabel()
        self.question.setWordWrap(True)
        self.question.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.suggestion_rows = QVBoxLayout()
        self.accept_all_button = QPushButton(T.PLAN_ACCEPT_ALL)
        self.accept_all_button.clicked.connect(self._accept_all)
        reply_row = QHBoxLayout()
        self.reply = QLineEdit()
        self.reply.setPlaceholderText(T.PLAN_REPLY_PLACEHOLDER)
        self.reply.setAccessibleName(T.PLAN_REPLY_A11Y)
        self.reply.setMaxLength(1000)
        self.reply.returnPressed.connect(self._send_reply)
        self.reply.textChanged.connect(lambda _text: self._sync_buttons())
        self.reply_button = QPushButton(T.PLAN_REPLY_SEND)
        self.reply_button.clicked.connect(self._send_reply)
        reply_row.addWidget(self.reply, 1)
        reply_row.addWidget(self.reply_button)
        helper_layout.addWidget(self.question)
        helper_layout.addLayout(self.suggestion_rows)
        helper_layout.addWidget(self.accept_all_button, 0, Qt.AlignmentFlag.AlignRight)
        helper_layout.addLayout(reply_row)

        todo_card, todo_layout = card(T.PLAN_TODO_SECTION)
        self.progress_label = QLabel()
        self.progress_label.setProperty("role", "subheading")
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.todos = QListWidget()
        self.todos.setAccessibleName(T.PLAN_TODO_A11Y)
        self.todos.setMinimumHeight(170)
        self.todos.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.todos.itemChanged.connect(self._item_changed)
        self.todos.currentRowChanged.connect(lambda _row: self._sync_buttons())
        add_row = QHBoxLayout()
        self.new_todo = QLineEdit()
        self.new_todo.setPlaceholderText(T.PLAN_ADD_PLACEHOLDER)
        self.new_todo.setAccessibleName(T.PLAN_ADD_A11Y)
        self.new_todo.setMaxLength(MAX_TODO_LENGTH)
        self.new_todo.returnPressed.connect(self._add_own_todo)
        self.new_todo.textChanged.connect(lambda _text: self._sync_buttons())
        self.add_button = QPushButton(T.PLAN_ADD)
        self.add_button.clicked.connect(self._add_own_todo)
        add_row.addWidget(self.new_todo, 1)
        add_row.addWidget(self.add_button)
        actions = QHBoxLayout()
        self.up_button = QPushButton(T.PLAN_MOVE_UP)
        self.up_button.setAccessibleName(T.PLAN_MOVE_UP_A11Y)
        self.up_button.clicked.connect(lambda: self._move_current(-1))
        self.down_button = QPushButton(T.PLAN_MOVE_DOWN)
        self.down_button.setAccessibleName(T.PLAN_MOVE_DOWN_A11Y)
        self.down_button.clicked.connect(lambda: self._move_current(1))
        self.remove_button = QPushButton(T.PLAN_REMOVE)
        self.remove_button.clicked.connect(self._remove_current)
        actions.addWidget(self.up_button)
        actions.addWidget(self.down_button)
        actions.addStretch(1)
        actions.addWidget(self.remove_button)
        todo_layout.addWidget(self.progress_label)
        todo_layout.addWidget(self.progress)
        todo_layout.addWidget(self.todos)
        todo_layout.addLayout(add_row)
        todo_layout.addLayout(actions)

        layout.addWidget(heading)
        layout.addWidget(intro)
        layout.addWidget(idea_card)
        layout.addWidget(self.message)
        layout.addWidget(self.helper_card)
        layout.addWidget(todo_card)
        layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self.content = content
        self.content.setEnabled(False)
        self._render_all()

    def load(self, plan: ProjectPlan) -> None:
        """Show the plan of the project that was just opened; an old request is forgotten."""
        self.plan = plan
        self._has_project = True
        self._busy = False
        self.content.setEnabled(True)
        self.description.blockSignals(True)
        self.description.setPlainText(plan.description)
        self.description.blockSignals(False)
        self.reply.clear()
        self.new_todo.clear()
        self._set_message("", "neutral")
        self._render_all()

    def set_language(self, language: str) -> None:
        python = language == "python"
        self.description.setPlaceholderText(
            T.PLAN_IDEA_PLACEHOLDER_PYTHON if python else T.PLAN_IDEA_PLACEHOLDER
        )

    def set_available(self, online: bool) -> None:
        self._online = online
        self._sync_buttons()
