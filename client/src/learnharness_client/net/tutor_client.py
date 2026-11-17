"""Qt signal-based interface shared by fake and network tutor clients."""

from __future__ import annotations

from dataclasses import dataclass

from learnharness_protocol import CodeSubmission, StudentMessage, Submission
from PyQt6.QtCore import QObject, pyqtSignal


@dataclass(frozen=True, slots=True)
class ClientError:
    message_for_child: str
    technical_code: str = "client_error"
    retryable: bool = True


class TutorClient(QObject):
    health_changed = pyqtSignal(object)
    session_started = pyqtSignal(object)
    task_received = pyqtSignal(object)
    stream_started = pyqtSignal()
    stream_chunk = pyqtSignal(str)
    stream_finished = pyqtSignal(object)
    exercise_received = pyqtSignal(object)
    review_received = pyqtSignal(object)
    progress_received = pyqtSignal(object)
    error = pyqtSignal(object)

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
