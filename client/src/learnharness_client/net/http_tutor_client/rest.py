"""HTTP requests to the learning server."""

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
    Submission,
    Task,
)
from pydantic import ValidationError
from PyQt6.QtCore import QByteArray, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from ...texts import T
from ..tutor_client import ClientError, TutorClient

LOG = logging.getLogger(__name__)


class HttpRestClient(TutorClient):
    """All requests that do not use the WebSocket."""

    MAX_MESSAGE_BYTES: int
    base_url: str
    token: str
    network: QNetworkAccessManager
    session_id: str | None

    def _url(self, path: str) -> QUrl:
        return QUrl(f"{self.base_url}/api/v1{path}")

    def _authorize(self, request: QNetworkRequest) -> QNetworkRequest:
        if self.token:
            request.setRawHeader(b"Authorization", f"Bearer {self.token}".encode())
        return request

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, object] | None,
        handler: Callable[[dict[str, object]], None],
        on_failure: Callable[[ClientError], None] | None = None,
    ) -> None:
        request = self._authorize(QNetworkRequest(self._url(path)))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setTransferTimeout(10_000)
        body = QByteArray(json.dumps(payload or {}, ensure_ascii=False).encode("utf-8"))
        if method == "GET":
            reply = self.network.get(request)
        else:
            reply = self.network.sendCustomRequest(request, method.encode("ascii"), body)
        assert reply is not None
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
                fail(ClientError(T.NET_UNREACHABLE, "network_error"))
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
            fail(ClientError(T.NET_TROUBLE, "invalid_response"))
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

    def request_next_hint(self, task_id: str) -> None:
        if not self.session_id:
            self.error.emit(ClientError(T.NET_NO_SESSION, "no_session"))
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
        query = f"?session_id={self.session_id}" if self.session_id else ""
        self._request(
            "GET",
            f"/progress{query}",
            None,
            lambda data: self.progress_received.emit(ProgressUpdate.model_validate(data)),
        )
