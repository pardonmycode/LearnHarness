"""Timing, health, session and streaming of the fake server."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial

from learnharness_protocol import (
    GeneratedFile,
    HealthStatus,
    LearningResponse,
    ReviewResult,
    SessionInfo,
)
from PyQt6.QtCore import QObject, QTimer

from .. import fake_content
from ..tutor_client import ClientError, TutorClient
from .level_exercises import FakeExercises


class FakeClientBase(FakeExercises, TutorClient):
    """Shared behaviour of the fake server."""

    def __init__(self, parent: QObject | None = None, *, delay_ms: int = 90) -> None:
        super().__init__(parent)  # type: ignore[arg-type]  # see qtcompat
        self.delay_ms = delay_ms
        self.session_id = "fake-session-001"
        self.hint_level = 0
        self.experience_level = 0
        self._learn_level: int | None = None
        self._learn_file = "player.gd"
        self._mission_file = "player.gd"
        self._generic_mission_steps: dict[str, fake_content.MissionStepContent] = {}
        self._cancelled = False
        self.simulate_failure = False

    def _later(self, callback: Callable[[], None], steps: int = 1) -> None:
        QTimer.singleShot(self.delay_ms * steps, callback)

    def check_health(self) -> None:
        if self.simulate_failure:
            self._later(
                lambda: self.health_changed.emit(HealthStatus(server_ok=False, model_ok=False))
            )
            return
        self._later(
            lambda: self.health_changed.emit(
                HealthStatus(server_ok=True, model_ok=True, session_active=True, latency_ms=8)
            )
        )

    def start_session(
        self,
        project_id: str,
        student_profile_id: str,
        student_pseudonym: str,
        experience_level: int,
    ) -> None:
        del project_id, student_profile_id
        self.experience_level = experience_level
        self._later(
            lambda: self.session_started.emit(
                SessionInfo(
                    session_id=self.session_id,
                    student_pseudonym=student_pseudonym,
                    current_task_id="move_player_right",
                )
            )
        )

    def _stream_text(self, text: str, response: LearningResponse) -> None:
        self._cancelled = False
        self.stream_started.emit()
        words = text.split(" ")
        for index, word in enumerate(words, start=1):
            chunk = word + (" " if index < len(words) else "")
            self._later(partial(self._emit_chunk, chunk), index)
        self._later(lambda: self._finish_stream(response), len(words) + 1)

    def _emit_chunk(self, text: str) -> None:
        if not self._cancelled:
            self.stream_chunk.emit(text)

    def _finish_stream(self, response: LearningResponse) -> None:
        if not self._cancelled:
            self.stream_finished.emit(response)

    def cancel(self) -> None:
        self._cancelled = True
        self.error.emit(ClientError("Die Antwort wurde gestoppt.", "cancelled", False))

    def _review(
        self, correct: bool, feedback: str, generated: list[GeneratedFile] | None = None
    ) -> None:
        result = ReviewResult(correct=correct, feedback=feedback, generated_files=generated or [])
        self._later(lambda: self.review_received.emit(result))
