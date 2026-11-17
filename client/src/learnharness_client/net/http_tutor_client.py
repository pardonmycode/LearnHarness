"""HTTP and WebSocket implementation for a Tailscale-reachable learning server."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable

from learnharness_protocol import (
    CodeSubmission,
    HealthStatus,
    HintRequest,
    LearningResponse,
    ProgressUpdate,
    ReviewResult,
    SessionCreate,
    SessionInfo,
    StudentMessage,
    Submission,
    Task,
)
from learnharness_protocol.messages import IncomingMessage, StreamChunk
from pydantic import TypeAdapter, ValidationError
from PyQt6.QtCore import QByteArray, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt6.QtWebSockets import QWebSocket

from learnharness_client import __version__

from .tutor_client import ClientError, TutorClient

LOG = logging.getLogger(__name__)


class HttpTutorClient(TutorClient):
    MAX_MESSAGE_BYTES = 256 * 1024

    def __init__(self, base_url: str, parent=None) -> None:
        super().__init__(parent)
        self.base_url = base_url.rstrip("/")
        self.network = QNetworkAccessManager(self)
        self.socket = QWebSocket(parent=self)
        self.session_id: str | None = None
        self._pending_message: StudentMessage | None = None
        self.socket.connected.connect(self._send_pending_message)
        self.socket.textMessageReceived.connect(self._on_socket_text)
        self.socket.errorOccurred.connect(self._on_socket_error)
        self.socket.disconnected.connect(self._on_socket_disconnected)

    def _url(self, path: str) -> QUrl:
        return QUrl(f"{self.base_url}/api/v1{path}")

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, object] | None,
        handler: Callable[[dict[str, object]], None],
        on_failure: Callable[[ClientError], None] | None = None,
    ) -> None:
        request = QNetworkRequest(self._url(path))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setTransferTimeout(10_000)
        body = QByteArray(json.dumps(payload or {}, ensure_ascii=False).encode("utf-8"))
        if method == "GET":
            reply = self.network.get(request)
        else:
            reply = self.network.sendCustomRequest(request, method.encode("ascii"), body)
        reply.finished.connect(
            lambda current=reply: self._finish_reply(current, handler, on_failure)
        )

    def _finish_reply(
        self,
        reply: QNetworkReply,
        handler: Callable[[dict[str, object]], None],
        on_failure: Callable[[ClientError], None] | None = None,
    ) -> None:
        fail = on_failure or self.error.emit
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                fail(ClientError("Der Lernhelfer ist gerade nicht erreichbar.", "network_error"))
                return
            raw = bytes(reply.readAll())
            if len(raw) > self.MAX_MESSAGE_BYTES:
                raise ValueError("response_too_large")
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("invalid_response")
            handler(data)
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError, ValueError) as exc:
            LOG.warning("Invalid learning-server response: %s", type(exc).__name__)
            fail(ClientError("Der Lernhelfer hat gerade Schwierigkeiten.", "invalid_response"))
        finally:
            reply.deleteLater()

    def check_health(self) -> None:
        self._request(
            "GET",
            "/health",
            None,
            lambda data: self.health_changed.emit(HealthStatus.model_validate(data)),
            # A failed background health check is a status change, not a chat message.
            lambda _error: self.health_changed.emit(HealthStatus(server_ok=False, model_ok=False)),
        )

    def start_session(
        self,
        project_id: str,
        student_profile_id: str,
        student_pseudonym: str,
        experience_level: int,
    ) -> None:
        payload = SessionCreate(
            project_id=project_id,
            client_version=__version__,
            student_profile_id=student_profile_id,
            student_pseudonym=student_pseudonym,
            experience_level=experience_level,
        ).model_dump()

        def finished(data: dict[str, object]) -> None:
            session = SessionInfo.model_validate(data)
            self.session_id = session.session_id
            self.session_started.emit(session)

        self._request("POST", "/sessions", payload, finished)

    def send_message(self, message: StudentMessage) -> None:
        raw = message.model_dump_json().encode("utf-8")
        if len(raw) > self.MAX_MESSAGE_BYTES:
            self.error.emit(ClientError("Der ausgewählte Codeausschnitt ist zu groß.", "too_large"))
            return
        self._pending_message = message
        self.stream_started.emit()
        if self.socket.isValid() and self.socket.state().name == "ConnectedState":
            self._send_pending_message()
            return
        http_url = QUrl(self.base_url)
        scheme = "wss" if http_url.scheme() == "https" else "ws"
        http_url.setScheme(scheme)
        http_url.setPath(f"/api/v1/sessions/{message.session_id}/stream")
        self.socket.open(http_url)

    def _send_pending_message(self) -> None:
        if self._pending_message is not None:
            self.socket.sendTextMessage(self._pending_message.model_dump_json())
            self._pending_message = None

    def _on_socket_text(self, text: str) -> None:
        if len(text.encode("utf-8")) > self.MAX_MESSAGE_BYTES:
            self.error.emit(ClientError("Die Serverantwort war zu groß.", "too_large"))
            return
        try:
            message = TypeAdapter(IncomingMessage).validate_json(text)
        except ValidationError as exc:
            LOG.warning("Rejected WebSocket payload: %s", type(exc).__name__)
            self.error.emit(
                ClientError("Der Lernhelfer hat gerade Schwierigkeiten.", "invalid_message")
            )
            return
        if isinstance(message, StreamChunk):
            self.stream_chunk.emit(message.text)
        elif isinstance(message, LearningResponse):
            self.stream_finished.emit(message)
        elif isinstance(message, Task):
            self.task_received.emit(message)
        else:
            self.error.emit(ClientError(message.message_for_child, message.code))

    def _on_socket_error(self, _error) -> None:
        self.error.emit(ClientError("Die Verbindung zum Lernhelfer wurde unterbrochen.", "socket"))

    def _on_socket_disconnected(self) -> None:
        self._pending_message = None

    def cancel(self) -> None:
        self._pending_message = None
        self.socket.close()

    def request_next_hint(self, task_id: str) -> None:
        if not self.session_id:
            self.error.emit(ClientError("Es gibt noch keine Lernsitzung.", "no_session"))
            return
        payload = HintRequest(task_id=task_id).model_dump()
        self._request(
            "POST",
            f"/sessions/{self.session_id}/hints",
            payload,
            lambda data: self.stream_finished.emit(LearningResponse.model_validate(data)),
        )

    def fetch_task(self, task_id: str) -> None:
        self._request(
            "GET",
            f"/tasks/{task_id}",
            None,
            lambda data: self.task_received.emit(Task.model_validate(data)),
        )

    def submit_exercise(self, submission: Submission) -> None:
        self._request(
            "POST",
            f"/exercises/{submission.exercise_id}/submissions",
            submission.model_dump(),
            lambda data: self.review_received.emit(ReviewResult.model_validate(data)),
        )

    def submit_code(self, submission: CodeSubmission) -> None:
        self._request(
            "POST",
            f"/tasks/{submission.task_id}/submissions",
            submission.model_dump(),
            lambda data: self.review_received.emit(ReviewResult.model_validate(data)),
        )

    def fetch_progress(self) -> None:
        self._request(
            "GET",
            "/progress",
            None,
            lambda data: self.progress_received.emit(ProgressUpdate.model_validate(data)),
        )
