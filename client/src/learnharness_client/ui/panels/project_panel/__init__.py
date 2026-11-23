"""Describe the project and make the idea clearer by answering the helper's questions."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from learnharness_client import design
from learnharness_client.domain.project_plan import MAX_ANSWER, ProjectPlan

from ....texts import T
from ..learn_agent_panel import card
from .planning import PanelPlanning
from .rendering import PanelRendering

__all__ = ["ProjectPanel"]


class ProjectPanel(PanelPlanning, PanelRendering, QWidget):
    plan_requested = pyqtSignal(str)  # the description or the child's answer
    plan_changed = pyqtSignal(dict)  # JSON-ready state for saving
    build_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.plan = ProjectPlan()
        self._online = True
        self._busy = False
        self._has_project = False
        self._pending_answer: str | None = None
        self._asked_description = ""

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(*design.PANEL_MARGINS)
        layout.setSpacing(design.PANEL_SPACING)
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
        self.description.setMinimumHeight(design.PROJECT_DESCRIPTION_MIN_HEIGHT)
        self.description.textChanged.connect(self._description_changed)
        self.plan_button = QPushButton(T.PLAN_START)
        self.plan_button.clicked.connect(self._request_from_description)
        self.build_button = QPushButton(T.PLAN_BUILD)
        self.build_button.setToolTip(T.PLAN_BUILD_TIP)
        self.build_button.clicked.connect(self.build_requested)
        idea_row = QHBoxLayout()
        idea_row.addStretch(1)
        idea_row.addWidget(self.plan_button)
        idea_row.addWidget(self.build_button)
        idea_layout.addWidget(self.description)
        idea_layout.addLayout(idea_row)

        self.message = QLabel()
        self.message.setWordWrap(True)
        self.message.setProperty("callout", "neutral")
        self.message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.message.hide()

        self.suggestion_card, suggestion_layout = card(T.PLAN_SUGGESTION_SECTION)
        self.suggestion = QLabel()
        self.suggestion.setWordWrap(True)
        self.suggestion.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.accept_button = QPushButton(T.PLAN_ACCEPT)
        self.accept_button.setProperty("primary", "true")
        self.accept_button.clicked.connect(self._accept_suggestion)
        self.reject_button = QPushButton(T.PLAN_REJECT)
        self.reject_button.clicked.connect(self._reject_suggestion)
        suggestion_row = QHBoxLayout()
        suggestion_row.addStretch(1)
        suggestion_row.addWidget(self.reject_button)
        suggestion_row.addWidget(self.accept_button)
        suggestion_layout.addWidget(self.suggestion)
        suggestion_layout.addLayout(suggestion_row)

        self.helper_card, helper_layout = card(T.PLAN_HELPER_SECTION)
        self.question = QLabel()
        self.question.setWordWrap(True)
        self.question.setProperty("role", "subheading")
        self.question.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.ready_label = QLabel(T.PLAN_READY)
        self.ready_label.setWordWrap(True)
        self.ready_label.setProperty("callout", "success")
        reply_row = QHBoxLayout()
        self.reply = QLineEdit()
        self.reply.setPlaceholderText(T.PLAN_REPLY_PLACEHOLDER)
        self.reply.setAccessibleName(T.PLAN_REPLY_A11Y)
        self.reply.setMaxLength(MAX_ANSWER)
        self.reply.returnPressed.connect(self._send_reply)
        self.reply.textChanged.connect(lambda _text: self._sync_buttons())
        self.reply_button = QPushButton(T.PLAN_REPLY_SEND)
        self.reply_button.setProperty("primary", "true")
        self.reply_button.clicked.connect(self._send_reply)
        reply_row.addWidget(self.reply, 1)
        reply_row.addWidget(self.reply_button)
        helper_layout.addWidget(self.question)
        helper_layout.addWidget(self.ready_label)
        helper_layout.addLayout(reply_row)

        layout.addWidget(heading)
        layout.addWidget(intro)
        layout.addWidget(idea_card)
        layout.addWidget(self.message)
        layout.addWidget(self.suggestion_card)
        layout.addWidget(self.helper_card)
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
        self._pending_answer = None
        self.content.setEnabled(True)
        self.description.blockSignals(True)
        self.description.setPlainText(plan.description)
        self.description.blockSignals(False)
        self.reply.clear()
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
