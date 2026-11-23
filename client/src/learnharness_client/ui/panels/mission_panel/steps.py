"""Working through the steps of a mission, one clear action at a time."""

from __future__ import annotations

from learnharness_protocol import LearningResponse, MissionList, MissionStep, ReviewResult

from ....texts import T
from .step_view import ANSWERING, EXPLAINED, LOADING, PASSED, READY


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

    def _continue(self) -> None:
        """The one main button: what it does depends on where the child is."""
        step = self.next_step()
        if self.mission is None or self._busy:
            return
        if self._phase == PASSED:
            self._advance()
        elif step is None:
            return
        elif self._phase == EXPLAINED:
            self._finish_step(self.active_step or step)
            self._advance()
        elif step.kind == "try":
            # Trying it out cannot be checked by the server; the child confirms it.
            self._finish_step(step)
            self._advance()
        elif self._phase == READY:
            self._request_step(step)

    def _advance(self) -> None:
        step = self.next_step()
        if step is None:
            return
        self.exercises.clear()
        self._phase = READY
        if step.kind == "try":
            self._shown_step = step
            self._render()
            self._reveal(self.step_button)
        else:
            self._request_step(step)

    def _request_step(self, step: MissionStep) -> None:
        if not self._online or self.mission is None:
            self._render()
            return
        self.active_step = step
        self._shown_step = step
        self.exercises.clear()
        self._phase = LOADING
        self._set_message(T.MISSION_STEP_LOADING, "neutral")
        self._set_busy(True)
        self._render()
        self.step_requested.emit(self.mission.id, step.id)

    def show_step_response(self, response: LearningResponse) -> None:
        self._set_busy(False)
        if response.mission is not None:
            self.show_mission(response.mission)
            self._set_message(response.message, "info")
            return
        self._set_message(response.message, "info")
        if response.exercise is not None:
            self._phase = ANSWERING
            self._render()
            self._reveal(self.exercises.show(response.exercise))
            return
        # A pure explanation stays on screen until the child has read it.
        explained = self.active_step is not None and self.active_step.kind != "exercise"
        self._phase = EXPLAINED if explained else READY
        self._render()
        self._reveal(self.step_button)

    def show_review(self, review: ReviewResult) -> None:
        self.exercises.show_result(review)
        if review.correct and self.active_step is not None:
            self._finish_step(self.active_step)
        elif not review.correct:
            self._set_message(T.MISSION_NOT_YET, "error")

    def _finish_step(self, step: MissionStep) -> None:
        self.done.add(step.id)
        self.active_step = None
        self._shown_step = step
        following = self.next_step()
        self._phase = PASSED if following is not None else READY
        if following is not None:
            # The exercise itself shows the feedback right below.
            self._set_message(T.MISSION_STEP_DONE, "success")
        self._render()  # shows the completion message when this was the last step
        self._reveal(self.step_button)
        self._emit_progress()
        if following is None and self.mission is not None:
            self.completed_ids.add(self.mission.id)
            if any(mission.id == self.mission.id for mission in self.assigned):
                self.set_assigned(MissionList(missions=self.assigned))  # shows the check mark
            self.mission_completed.emit(self.mission.id)

    def show_error(self, message: str) -> None:
        self._set_busy(False)
        self.exercises.submission_failed()
        if self._phase == LOADING:
            self._phase = READY  # the button offers the same step again
            self._render()
        self._set_message(message, "error")

    def set_project_idea(self, has_idea: bool) -> None:
        if has_idea != self._has_project_idea:
            self._has_project_idea = has_idea
            self._render()

    def _next_project_mission(self) -> None:
        if self._busy or not self._online:
            return
        self.reset()
        self.request_mission(T.MISSION_PROJECT_WISH)
