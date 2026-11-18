"""Level-based LearnAgent that gates generated code behind learning checks."""

from __future__ import annotations

from learnharness_protocol import LearningResponse, ReviewResult
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItemModel
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

from ...texts import T
from ..exercises.base import ExerciseWidget
from ..exercises.factory import create_exercise_widget
from ..theme import set_state

LEVEL_DESCRIPTIONS = T.LEVEL_DESCRIPTIONS


def card(title: str) -> tuple[QFrame, QVBoxLayout]:
    """Rounded surface with a small section title."""
    frame = QFrame()
    frame.setProperty("card", "true")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(8)
    label = QLabel(title)
    label.setProperty("role", "section")
    layout.addWidget(label)
    return frame, layout


class LearnAgentPanel(QWidget):
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
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        heading = QLabel(T.AGENT_HEADING)
        heading.setProperty("role", "heading")
        intro = QLabel(T.AGENT_INTRO)
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")

        level_card, level_layout = card(T.AGENT_LEVEL_SECTION)
        level_row = QHBoxLayout()
        self.level_choice = QComboBox()
        self.level_choice.setAccessibleName(T.AGENT_LEVEL_A11Y)
        self.level_choice.setMinimumWidth(150)
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

        wish_card, wish_layout = card(T.AGENT_WISH_SECTION)
        self.prompt = QPlainTextEdit()
        self.prompt.setPlaceholderText(T.AGENT_WISH_PLACEHOLDER)
        self.prompt.setFixedHeight(90)
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

    def set_available(self, online: bool) -> None:
        self._online = online
        self._sync_start_button()

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._sync_start_button()

    def _sync_start_button(self) -> None:
        self.start_button.setEnabled(self._online and not self._busy)
        self.start_button.setToolTip("" if self._online else T.AGENT_OFFLINE_TIP)

    @property
    def current_level(self) -> int:
        return int(self.level_choice.currentData())

    def set_max_unlocked(self, level: int) -> None:
        self.max_unlocked_level = max(1, min(10, level))
        model = self.level_choice.model()
        if isinstance(model, QStandardItemModel):
            for index in range(self.level_choice.count()):
                item = model.item(index)
                item.setEnabled(index + 1 <= self.max_unlocked_level)
                label = T.AGENT_LEVEL if item.isEnabled() else T.AGENT_LEVEL_LOCKED
                item.setText(label.format(level=index + 1))
        self.progress.setValue(self.max_unlocked_level)
        if self.level_choice.currentIndex() + 1 > self.max_unlocked_level:
            # A teacher lowered the level: jump to the highest level still unlocked.
            self.level_choice.setCurrentIndex(self.max_unlocked_level - 1)
        self.unlocked_label.setText(T.AGENT_UNLOCKED.format(level=self.max_unlocked_level))

    def _level_changed(self) -> None:
        level = self.current_level
        if level > self.max_unlocked_level:
            self.level_choice.setCurrentIndex(self.max_unlocked_level - 1)
            return
        self.level_description.setText(LEVEL_DESCRIPTIONS[level])
        self.clear_exercise()
        self._set_feedback("", "")

    def _set_feedback(self, text: str, state: str) -> None:
        self.feedback.setText(text)
        self.feedback.setVisible(bool(text))
        set_state(self.feedback, callout=state or "neutral")

    def _start(self) -> None:
        prompt = self.prompt.toPlainText().strip()
        if not prompt:
            self._set_feedback(T.AGENT_WISH_EMPTY, "error")
            return
        self._set_busy(True)
        self.clear_exercise()
        self._set_feedback(T.AGENT_PREPARING, "neutral")
        self.start_requested.emit(prompt, self.current_level)

    def show_response(self, response: LearningResponse) -> None:
        self._set_busy(False)
        self._set_feedback(response.message, "info")
        if response.exercise is not None:
            self.show_exercise(response.exercise)

    def show_exercise(self, exercise) -> None:
        self.clear_exercise()
        widget = create_exercise_widget(exercise, self.exercise_host)
        self.exercise_widget = widget
        self.exercise_layout.addWidget(widget)
        if isinstance(widget, ExerciseWidget):
            widget.submitted.connect(self.exercise_submitted)
        self._scroll.ensureWidgetVisible(widget)

    def show_review(self, review: ReviewResult) -> None:
        if isinstance(self.exercise_widget, ExerciseWidget):
            self.exercise_widget.show_result(review)
        if review.correct:
            self._set_feedback(T.AGENT_CORRECT, "success")
        else:
            self._set_feedback(T.AGENT_NOT_YET, "error")

    def show_code_result(self, written_files: list[str], explanations: list[str]) -> None:
        if written_files:
            names = ", ".join(written_files)
            explanation = "\n\n".join(explanations)
            self._set_feedback(
                T.AGENT_CODE_WRITTEN.format(files=names, explanation=explanation), "success"
            )
        else:
            self._set_feedback(T.AGENT_CODE_FAILED, "error")

    def show_error(self, message: str) -> None:
        self._set_busy(False)
        if isinstance(self.exercise_widget, ExerciseWidget):
            self.exercise_widget.submission_failed()
        self._set_feedback(message, "error")

    def clear_exercise(self) -> None:
        if self.exercise_widget is not None:
            self.exercise_layout.removeWidget(self.exercise_widget)
            self.exercise_widget.deleteLater()
            self.exercise_widget = None
