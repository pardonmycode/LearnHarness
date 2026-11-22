"""Starting a round and showing its results."""

from __future__ import annotations

from learnharness_protocol import LearningResponse, ReviewResult

from ....texts import T
from ...exercises.base import ExerciseWidget
from ...exercises.factory import create_exercise_widget
from ...theme import set_state


class AgentRounds:
    """One learning round."""

    def set_available(self, online: bool) -> None:
        self._online = online
        self._sync_start_button()

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._sync_start_button()

    def _sync_start_button(self) -> None:
        self.start_button.setEnabled(self._online and not self._busy)
        self.start_button.setToolTip("" if self._online else T.AGENT_OFFLINE_TIP)

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
