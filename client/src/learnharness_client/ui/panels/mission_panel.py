"""Learning missions: a small goal worked through step by step."""

from __future__ import annotations

from learnharness_protocol import (
    LearningResponse,
    Mission,
    MissionList,
    MissionStep,
    ReviewResult,
)
from pydantic import ValidationError
from PyQt6.QtCore import Qt, pyqtSignal
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

from ...texts import T
from ..theme import set_state
from .exercise_host import ExerciseHost
from .learn_agent_panel import card


class MissionPanel(QWidget):
    mission_requested = pyqtSignal(str)  # wish
    step_requested = pyqtSignal(str, str)  # mission id, step id
    exercise_submitted = pyqtSignal(object)
    progress_changed = pyqtSignal(dict)  # JSON-ready state for saving
    mission_completed = pyqtSignal(str)  # mission id

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.mission: Mission | None = None
        self.done: set[str] = set()
        self.active_step: MissionStep | None = None
        self._online = True
        self._busy = False

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        heading = QLabel(T.MISSION_HEADING)
        heading.setProperty("role", "heading")
        intro = QLabel(T.MISSION_INTRO)
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")

        self.assigned: list[Mission] = []
        self.completed_ids: set[str] = set()
        self.assigned_card, assigned_layout = card(T.MISSION_ASSIGNED_HEADING)
        self.assigned_buttons = QVBoxLayout()
        assigned_layout.addLayout(self.assigned_buttons)
        self.assigned_card.hide()

        self.choose_card, choose_layout = card(T.MISSION_OWN_HEADING)
        for suggestion in T.MISSION_SUGGESTIONS:
            button = QPushButton(suggestion)
            button.clicked.connect(lambda _=False, text=suggestion: self.request_mission(text))
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
        self.step_button = QPushButton(T.MISSION_DO_STEP)
        self.step_button.setProperty("primary", "true")
        self.step_button.clicked.connect(self._start_step)
        self.new_button = QPushButton(T.MISSION_NEW)
        self.new_button.clicked.connect(self.reset)
        buttons = QHBoxLayout()
        buttons.addWidget(self.new_button)
        buttons.addStretch(1)
        buttons.addWidget(self.step_button)
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

        layout.addWidget(heading)
        layout.addWidget(intro)
        layout.addWidget(self.assigned_card)
        layout.addWidget(self.choose_card)
        layout.addWidget(self.mission_card)
        layout.addWidget(self.message)
        layout.addWidget(self.exercises.widget)
        layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self._scroll = scroll

    # Choosing a mission ------------------------------------------------------------

    def request_mission(self, wish: str) -> None:
        wish = wish.strip()
        if not wish or self._busy or not self._online:
            return
        self._set_busy(True)
        self._set_message(T.MISSION_STARTING, "neutral")
        self.mission_requested.emit(wish)

    def set_assigned(self, listing: MissionList) -> None:
        """Missions from the teacher; finished ones stay visible with a check mark."""
        self.assigned = list(listing.missions)
        self.completed_ids |= set(listing.completed)
        while self.assigned_buttons.count():
            item = self.assigned_buttons.takeAt(0)
            if item is not None and item.widget() is not None:
                item.widget().deleteLater()  # type: ignore[union-attr]
        for mission in self.assigned:
            done = mission.id in self.completed_ids
            button = QPushButton(
                T.MISSION_ASSIGNED_DONE.format(title=mission.title) if done else mission.title
            )
            button.setToolTip(mission.goal)
            if done:
                button.setAccessibleName(T.MISSION_ASSIGNED_A11Y_DONE.format(title=mission.title))
            button.clicked.connect(lambda _=False, chosen=mission: self.start_assigned(chosen))
            self.assigned_buttons.addWidget(button)
        self._render()

    def assigned_titles(self) -> list[str]:
        texts = []
        for index in range(self.assigned_buttons.count()):
            item = self.assigned_buttons.itemAt(index)
            widget = item.widget() if item else None
            if isinstance(widget, QPushButton):
                texts.append(widget.text())
        return texts

    def start_assigned(self, mission: Mission) -> None:
        """The teacher's missions are known already: no server round trip to start them."""
        if self._busy:
            return
        self.show_mission(mission)
        self._set_message(T.MISSION_ASSIGNED_START.format(goal=mission.goal), "info")

    def show_mission(self, mission: Mission, done: set[str] | None = None) -> None:
        self._set_busy(False)
        self.mission = mission
        self.done = {step.id for step in mission.steps} & (done or set())
        self.active_step = None
        self.exercises.clear()
        self.message.hide()
        self.wish.clear()
        self._render()
        self._emit_progress()

    def reset(self) -> None:
        self.mission = None
        self.done = set()
        self.active_step = None
        self.exercises.clear()
        self.message.hide()
        self._render()
        self._emit_progress()

    # State ---------------------------------------------------------------------------

    def state(self) -> dict[str, object]:
        if self.mission is None:
            return {}
        return {"mission": self.mission.model_dump(mode="json"), "done": sorted(self.done)}

    def restore(self, state: dict[str, object]) -> None:
        try:
            mission = Mission.model_validate(state.get("mission"))
        except ValidationError:
            return
        done = state.get("done")
        self.show_mission(
            mission, {str(item) for item in done} if isinstance(done, list) else set()
        )

    def next_step(self) -> MissionStep | None:
        if self.mission is None:
            return None
        return next((step for step in self.mission.steps if step.id not in self.done), None)

    @property
    def complete(self) -> bool:
        return self.mission is not None and self.next_step() is None

    def _emit_progress(self) -> None:
        self.progress_changed.emit(self.state())

    def _render(self) -> None:
        self.choose_card.setVisible(self.mission is None)
        self.assigned_card.setVisible(self.mission is None and bool(self.assigned))
        self.mission_card.setVisible(self.mission is not None)
        while self.steps_box.count():
            item = self.steps_box.takeAt(0)
            if item is not None and item.widget() is not None:
                item.widget().deleteLater()  # type: ignore[union-attr]
        if self.mission is None:
            return
        if isinstance(self.mission_title, QLabel):
            self.mission_title.setText(self.mission.title)
        self.goal.setText(self.mission.goal)
        total = len(self.mission.steps)
        text = T.MISSION_PROGRESS.format(done=len(self.done), total=total)
        self.progress_label.setText(text)
        self.progress.setRange(0, total)
        self.progress.setValue(len(self.done))
        self.progress.setAccessibleName(text)
        current = self.next_step()
        for step in self.mission.steps:
            mark = "☑" if step.id in self.done else ("➜" if step is current else "☐")
            label = QLabel(f"{mark}  {step.title}")
            label.setWordWrap(True)
            if step is current:
                label.setProperty("role", "subheading")
            self.steps_box.addWidget(label)
        if current is None:
            self.step_button.hide()
            self._set_message(T.MISSION_COMPLETE.format(title=self.mission.title), "success")
            return
        self.step_button.show()
        self.step_button.setText(T.MISSION_TRY_DONE if current.kind == "try" else T.MISSION_DO_STEP)
        self._sync_buttons()

    # Working on steps ------------------------------------------------------------------

    def _start_step(self) -> None:
        step = self.next_step()
        if step is None or self.mission is None or self._busy:
            return
        if step.kind == "try":
            # Trying it in Godot cannot be checked by the server; the child confirms it.
            self._finish_step(step)
            return
        if not self._online:
            return
        self.active_step = step
        self.exercises.clear()
        self._set_busy(True)
        self._set_message(T.MISSION_STARTING, "neutral")
        self.step_requested.emit(self.mission.id, step.id)

    def show_step_response(self, response: LearningResponse) -> None:
        self._set_busy(False)
        if response.mission is not None:
            self.show_mission(response.mission)
            self._set_message(response.message, "info")
            return
        self._set_message(response.message, "info")
        if response.exercise is not None:
            widget = self.exercises.show(response.exercise)
            self._scroll.ensureWidgetVisible(widget)
        elif self.active_step is not None and self.active_step.kind != "exercise":
            # Pure explanation without a question: reading it completes the step.
            self._finish_step(self.active_step)

    def show_review(self, review: ReviewResult) -> None:
        self.exercises.show_result(review)
        if review.correct and self.active_step is not None:
            self._finish_step(self.active_step, review.feedback)
        elif not review.correct:
            self._set_message(T.MISSION_NOT_YET, "error")

    def _finish_step(self, step: MissionStep, feedback: str = "") -> None:
        self.done.add(step.id)
        self.active_step = None
        self._render()  # shows the completion message when this was the last step
        following = self.next_step()
        if following is not None:
            text = f"{T.MISSION_STEP_DONE} {feedback}".strip()
            if following.kind == "try":
                text += "\n\n" + T.MISSION_TRY_TEXT
            self._set_message(text, "success")
        self._emit_progress()
        if following is None and self.mission is not None:
            self.completed_ids.add(self.mission.id)
            if any(mission.id == self.mission.id for mission in self.assigned):
                self.set_assigned(MissionList(missions=self.assigned))  # shows the check mark
            self.mission_completed.emit(self.mission.id)

    def show_error(self, message: str) -> None:
        self._set_busy(False)
        self.exercises.submission_failed()
        self._set_message(message, "error")

    # Helpers ---------------------------------------------------------------------------

    def _set_message(self, text: str, state: str) -> None:
        self.message.setText(text)
        self.message.setVisible(bool(text))
        set_state(self.message, callout=state)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._sync_buttons()

    def set_available(self, online: bool) -> None:
        self._online = online
        self._sync_buttons()

    def _sync_buttons(self) -> None:
        enabled = self._online and not self._busy
        self.start_button.setEnabled(enabled)
        step = self.next_step()
        offline_ok = bool(step and step.kind == "try")  # needs no server
        self.step_button.setEnabled(not self._busy and (enabled or offline_ok))
