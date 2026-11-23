"""Level-based LearnAgent that gates generated code behind learning checks."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from learnharness_client import design

from ....texts import T
from .cards import card
from .levels import LEVEL_DESCRIPTIONS, AgentLevels
from .rounds import AgentRounds

__all__ = ["LEVEL_DESCRIPTIONS", "LearnAgentPanel", "card"]


class LearnAgentPanel(AgentLevels, AgentRounds, QWidget):
    start_requested = pyqtSignal(str, int)
    exercise_submitted = pyqtSignal(object)
    show_changes_toggled = pyqtSignal(bool)

    def __init__(self, max_unlocked_level: int, parent=None, *, show_changes: bool = True) -> None:
        super().__init__(parent)
        self.max_unlocked_level = max(1, min(10, max_unlocked_level))
        self.exercise_widget: QWidget | None = None
        self._online = True
        self._busy = False

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(*design.PANEL_MARGINS)
        layout.setSpacing(design.PANEL_SPACING)

        heading = QLabel(T.AGENT_HEADING)
        heading.setProperty("role", "heading")
        intro = QLabel(T.AGENT_INTRO)
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")

        level_card, level_layout = card(T.AGENT_LEVEL_SECTION)
        level_row = QHBoxLayout()
        self.level_choice = QComboBox()
        self.level_choice.setAccessibleName(T.AGENT_LEVEL_A11Y)
        self.level_choice.setMinimumWidth(design.LEVEL_CHOICE_MIN_WIDTH)
        for level in range(1, 11):
            self.level_choice.addItem(T.AGENT_LEVEL.format(level=level), level)
        self.unlocked_label = QLabel()
        self.unlocked_label.setProperty("role", "small")
        level_row.addWidget(self.level_choice)
        level_row.addStretch(1)
        level_row.addWidget(self.unlocked_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 10)
        self.progress.setTextVisible(False)
        self.progress.setAccessibleName(T.AGENT_UNLOCKED_A11Y)
        self.level_description = QLabel()
        self.level_description.setWordWrap(True)
        level_layout.addLayout(level_row)
        level_layout.addWidget(self.progress)
        level_layout.addWidget(self.level_description)

        focus_card, focus_layout = card(T.FOCUS_SECTION)
        self.focus_choice = QComboBox()
        self.focus_choice.setAccessibleName(T.FOCUS_A11Y)
        focus_hint = QLabel(T.FOCUS_HINT)
        focus_hint.setWordWrap(True)
        focus_hint.setProperty("role", "small")
        focus_layout.addWidget(self.focus_choice)
        focus_layout.addWidget(focus_hint)
        self._auto_focus: str | None = None
        self.set_skills([])

        wish_card, wish_layout = card(T.AGENT_WISH_SECTION)
        self.prompt = QPlainTextEdit()
        self.prompt.setPlaceholderText(T.AGENT_WISH_PLACEHOLDER)
        self.prompt.setFixedHeight(design.LEARN_PROMPT_HEIGHT)
        self.prompt.setAccessibleName(T.AGENT_WISH_A11Y)
        self.prompt.setTabChangesFocus(True)
        self.start_button = QPushButton(T.AGENT_START)
        self.start_button.setProperty("primary", "true")
        self.start_button.clicked.connect(self._start)
        self.changes_toggle = QPushButton(T.CHANGES_TOGGLE)
        self.changes_toggle.setCheckable(True)
        self.changes_toggle.setChecked(show_changes)
        self.changes_toggle.setToolTip(T.CHANGES_TOGGLE_TIP)
        self.changes_toggle.setAccessibleName(T.CHANGES_TOGGLE)
        self.changes_toggle.toggled.connect(self.show_changes_toggled)
        button_row = QHBoxLayout()
        button_row.addWidget(self.changes_toggle)
        button_row.addStretch(1)
        button_row.addWidget(self.start_button)
        wish_layout.addWidget(self.prompt)
        wish_layout.addLayout(button_row)

        self.feedback = QLabel()
        self.feedback.setWordWrap(True)
        self.feedback.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.feedback.hide()
        self.exercise_host = QWidget()
        self.exercise_layout = QVBoxLayout(self.exercise_host)
        self.exercise_layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(heading)
        layout.addWidget(intro)
        layout.addWidget(level_card)
        layout.addWidget(focus_card)
        layout.addWidget(wish_card)
        layout.addWidget(self.feedback)
        layout.addWidget(self.exercise_host)
        layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self._scroll = scroll

        self.level_choice.currentIndexChanged.connect(self._level_changed)
        self.set_max_unlocked(self.max_unlocked_level)
        self.level_choice.setCurrentIndex(self.max_unlocked_level - 1)
        self._level_changed()
