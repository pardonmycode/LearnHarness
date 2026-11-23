"""Learning missions: a small goal worked through step by step."""

from __future__ import annotations

from learnharness_protocol import Mission, MissionStep
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from learnharness_client import design

from ....texts import T
from ..exercise_host import ExerciseHost
from ..learn_agent_panel import card
from .choosing import MissionChoosing
from .step_view import READY, MissionStepView
from .steps import MissionSteps

__all__ = ["MissionPanel"]


class MissionPanel(MissionChoosing, MissionSteps, MissionStepView, QWidget):
    mission_requested = pyqtSignal(str)  # wish
    project_mission_requested = pyqtSignal()
    step_requested = pyqtSignal(str, str)  # mission id, step id
    exercise_submitted = pyqtSignal(object)
    progress_changed = pyqtSignal(dict)  # JSON-ready state for saving
    mission_completed = pyqtSignal(str)  # mission id
    help_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.mission: Mission | None = None
        self.done: set[str] = set()
        self.active_step: MissionStep | None = None
        self._online = True
        self._busy = False
        self._phase = READY
        self._shown_step: MissionStep | None = None
        self._has_project_idea = False
        self._reveal_target: QWidget | None = None
        self._reveal_timer = QTimer(self)
        self._reveal_timer.setSingleShot(True)
        self._reveal_timer.setInterval(0)
        self._reveal_timer.timeout.connect(self._scroll_to_target)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(*design.PANEL_MARGINS)
        layout.setSpacing(design.PANEL_SPACING)
        heading = QLabel(T.MISSION_HEADING)
        heading.setProperty("role", "heading")
        self.language = "gdscript"
        intro = QLabel(T.MISSION_INTRO)
        self.intro = intro
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")

        self.assigned: list[Mission] = []
        self.completed_ids: set[str] = set()
        self.assigned_card, assigned_layout = card(T.MISSION_ASSIGNED_HEADING)
        self.assigned_buttons = QVBoxLayout()
        assigned_layout.addLayout(self.assigned_buttons)
        self.assigned_card.hide()

        self.project_card, project_layout = card(T.MISSION_PROJECT_HEADING)
        project_text = QLabel(T.MISSION_PROJECT_TEXT)
        project_text.setWordWrap(True)
        self.project_button = QPushButton(T.MISSION_PROJECT_BUTTON)
        self.project_button.setProperty("primary", "true")
        self.project_button.clicked.connect(self._next_project_mission)
        project_layout.addWidget(project_text)
        project_layout.addWidget(self.project_button)
        self.project_card.hide()

        self.choose_card, choose_layout = card(T.MISSION_OWN_HEADING)
        self._suggestions: dict[str, list[QPushButton]] = {"gdscript": [], "python": []}
        for language, suggestions in (
            ("gdscript", T.MISSION_SUGGESTIONS),
            ("python", T.MISSION_SUGGESTIONS_PYTHON),
        ):
            for suggestion in suggestions:
                button = QPushButton(suggestion)
                button.clicked.connect(lambda _=False, text=suggestion: self.request_mission(text))
                button.setVisible(language == self.language)
                self._suggestions[language].append(button)
                choose_layout.addWidget(button)
        wish_row = QHBoxLayout()
        self.wish = QLineEdit()
        self.wish.setPlaceholderText(T.MISSION_WISH_PLACEHOLDER)
        self.wish.setAccessibleName(T.MISSION_WISH_A11Y)
        self.wish.returnPressed.connect(lambda: self.request_mission(self.wish.text()))
        self.start_button = QPushButton(T.MISSION_START)
        self.start_button.setProperty("primary", "true")
        self.start_button.clicked.connect(lambda: self.request_mission(self.wish.text()))
        wish_row.addWidget(self.wish, 1)
        wish_row.addWidget(self.start_button)
        choose_layout.addLayout(wish_row)

        self.mission_card, mission_layout = card("")
        self.mission_title = mission_layout.itemAt(0).widget()  # type: ignore[union-attr]
        self.goal = QLabel()
        self.goal.setWordWrap(True)
        self.progress_label = QLabel()
        self.progress_label.setProperty("role", "subheading")
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setAccessibleName(T.MISSION_PROGRESS.format(done=0, total=0))
        self.steps_box = QVBoxLayout()
        self.new_button = QPushButton(T.MISSION_NEW)
        self.new_button.clicked.connect(self.reset)
        buttons = QHBoxLayout()
        buttons.addWidget(self.new_button)
        buttons.addStretch(1)
        mission_layout.addWidget(self.goal)
        mission_layout.addWidget(self.progress_label)
        mission_layout.addWidget(self.progress)
        mission_layout.addLayout(self.steps_box)
        mission_layout.addLayout(buttons)
        self.mission_card.hide()

        self.message = QLabel()
        self.message.setWordWrap(True)
        self.message.setProperty("callout", "neutral")  # padding from the first layout on
        self.message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.message.hide()
        self.exercises = ExerciseHost(self)
        self.exercises.submitted.connect(self.exercise_submitted)

        # Everything about the current step, with its one next action at the bottom.
        self.step_card, step_layout = card("")
        self.step_title = step_layout.itemAt(0).widget()
        self.answer_hint = QLabel(T.MISSION_ANSWER_HINT)
        self.answer_hint.setWordWrap(True)
        self.answer_hint.setProperty("role", "muted")
        self.help_button = QPushButton(T.MISSION_TRY_HELP)
        self.help_button.clicked.connect(self.help_requested)
        self.next_project_button = QPushButton(T.MISSION_PROJECT_BUTTON)
        self.next_project_button.setProperty("primary", "true")
        self.next_project_button.clicked.connect(self._next_project_mission)
        self.step_button = QPushButton()
        self.step_button.setProperty("primary", "true")
        self.step_button.clicked.connect(self._continue)
        action_row = QHBoxLayout()
        action_row.addWidget(self.help_button)
        action_row.addStretch(1)
        action_row.addWidget(self.next_project_button)
        action_row.addWidget(self.step_button)
        step_layout.addWidget(self.message)
        step_layout.addWidget(self.exercises.widget)
        step_layout.addWidget(self.answer_hint)
        step_layout.addLayout(action_row)
        self.step_card.hide()
        self.help_button.hide()
        self.next_project_button.hide()
        self.answer_hint.hide()

        layout.addWidget(heading)
        layout.addWidget(intro)
        layout.addWidget(self.project_card)
        layout.addWidget(self.assigned_card)
        layout.addWidget(self.choose_card)
        layout.addWidget(self.mission_card)
        layout.addWidget(self.step_card)
        layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self._scroll = scroll
