"""Working through the steps of a mission."""

from __future__ import annotations

from learnharness_protocol import LearningResponse, MissionList, MissionStep, ReviewResult
from PyQt6.QtWidgets import QLabel

from ....texts import T
from ...theme import set_state


class MissionSteps:
    """Progress through the steps."""

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
        try_done = T.MISSION_TRY_DONE_PYTHON if self.language == "python" else T.MISSION_TRY_DONE
        self.step_button.setText(try_done if current.kind == "try" else T.MISSION_DO_STEP)
        self._sync_buttons()

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
                text += "\n\n" + (
                    T.MISSION_TRY_TEXT_PYTHON if self.language == "python" else T.MISSION_TRY_TEXT
                )
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
