"""Qt signal-based interface shared by fake and network tutor clients."""

from __future__ import annotations

from dataclasses import dataclass

from learnharness_protocol import CodeSubmission, StudentMessage, Submission
from PyQt6.QtCore import QObject

from ..qtcompat import signal


@dataclass(frozen=True, slots=True)
class ClientError:
    message_for_child: str
    technical_code: str = "client_error"
    retryable: bool = True


class TutorClient(QObject):
    health_changed = signal(object)
    session_started = signal(object)
    task_received = signal(object)
    stream_started = signal()
    stream_chunk = signal(str)
    stream_finished = signal(object)
    exercise_received = signal(object)
    review_received = signal(object)
    progress_received = signal(object)
    error = signal(object)

    def check_health(self) -> None:
        raise NotImplementedError

    def start_session(
        self,
        project_id: str,
        student_profile_id: str,
        student_pseudonym: str,
        experience_level: int,
    ) -> None:
        raise NotImplementedError

    def send_message(self, message: StudentMessage) -> None:
        raise NotImplementedError

    def cancel(self) -> None:
        raise NotImplementedError

    def request_next_hint(self, task_id: str) -> None:
        raise NotImplementedError

    def fetch_task(self, task_id: str) -> None:
        raise NotImplementedError

    def submit_exercise(self, submission: Submission) -> None:
        raise NotImplementedError

    def submit_code(self, submission: CodeSubmission) -> None:
        raise NotImplementedError

    def fetch_progress(self) -> None:
        raise NotImplementedError
