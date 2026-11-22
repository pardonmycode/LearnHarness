"""HTTP and WebSocket implementation for a Tailscale-reachable learning server."""

from __future__ import annotations

import logging

from learnharness_protocol import LearningResponse, SessionCreate, SessionInfo, StudentMessage, Task
from learnharness_protocol.messages import ErrorMessage, IncomingMessage, StreamChunk
from pydantic import TypeAdapter, ValidationError
from PyQt6.QtCore import QObject, QTimer, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWebSockets import QWebSocket

from learnharness_client import __version__

from ...texts import T
from ..tutor_client import ClientError
from .helpers import same_server
from .rest import HttpRestClient

__all__ = ["HttpTutorClient", "LOG", "same_server"]


LOG = logging.getLogger(__name__)


# mypy cannot express an Annotated discriminated union as ``type[...]``; the adapter type is exact.
_INCOMING: TypeAdapter[StreamChunk | LearningResponse | ErrorMessage | Task] = TypeAdapter(
    IncomingMessage  # type: ignore[arg-type, unused-ignore]  # needed only on some versions
)


class HttpTutorClient(HttpRestClient):
    MAX_MESSAGE_BYTES = 256 * 1024
    # Reconnect delays after an unexpected WebSocket loss; the last value repeats.
    RECONNECT_BACKOFF_MS = (1_000, 2_000, 5_000, 10_000, 30_000)

    def __init__(self, base_url: str, parent: QObject | None = None, token: str = "") -> None:
        super().__init__(parent)  # type: ignore[arg-type]  # see qtcompat
        self.base_url = base_url.rstrip("/")
        # Device token of the central administration; only sent when this learning server
        # is the administration itself (see same_server()).
        self.token = token.strip()
        self.network = QNetworkAccessManager(self)
        self.socket = QWebSocket(parent=self)
        self.session_id: str | None = None
        self._pending_message: StudentMessage | None = None
        self._stream_url: QUrl | None = None
        self._closing = False
        self._reconnect_attempt = 0
        self._outage_reported = False
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setSingleShot(True)
        self._reconnect_timer.timeout.connect(self._reconnect)
        self.socket.connected.connect(self._on_socket_connected)
        self.socket.textMessageReceived.connect(self._on_socket_text)
        self.socket.errorOccurred.connect(self._on_socket_error)
        self.socket.disconnected.connect(self._on_socket_disconnected)

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
            self.error.emit(ClientError(T.NET_EXCERPT_TOO_LARGE, "too_large"))
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
        self._stream_url = http_url
        self._reconnect_timer.stop()
        self._closing = False
        self.socket.open(self._authorize(QNetworkRequest(http_url)))

    @classmethod
    def reconnect_delay_ms(cls, attempt: int) -> int:
        """Delay before reconnect attempt number ``attempt`` (0-based): 1, 2, 5, 10, 30 s."""
        backoff = cls.RECONNECT_BACKOFF_MS
        return backoff[min(max(0, attempt), len(backoff) - 1)]

    def _on_socket_connected(self) -> None:
        self._reconnect_attempt = 0
        self._outage_reported = False
        self._reconnect_timer.stop()
        self._send_pending_message()

    def _schedule_reconnect(self) -> None:
        if self._closing or self._stream_url is None or not self.session_id:
            return
        if self._reconnect_timer.isActive():
            return
        delay = self.reconnect_delay_ms(self._reconnect_attempt)
        self._reconnect_attempt += 1
        LOG.info("WebSocket reconnect in %d ms", delay)
        self._reconnect_timer.start(delay)

    def _reconnect(self) -> None:
        if self._closing or self._stream_url is None:
            return
        self.socket.open(self._authorize(QNetworkRequest(self._stream_url)))

    def _send_pending_message(self) -> None:
        if self._pending_message is not None:
            self.socket.sendTextMessage(self._pending_message.model_dump_json())
            self._pending_message = None

    def _on_socket_text(self, text: str) -> None:
        if len(text.encode("utf-8")) > self.MAX_MESSAGE_BYTES:
            self.error.emit(ClientError(T.NET_RESPONSE_TOO_LARGE, "too_large"))
            return
        try:
            message = _INCOMING.validate_json(text)
        except ValidationError as exc:
            LOG.warning("Rejected WebSocket payload: %s", type(exc).__name__)
            self.error.emit(ClientError(T.NET_TROUBLE, "invalid_message"))
            return
        if isinstance(message, StreamChunk):
            self.stream_chunk.emit(message.text)
        elif isinstance(message, LearningResponse):
            self.stream_finished.emit(message)
        elif isinstance(message, Task):
            self.task_received.emit(message)
        else:
            self.error.emit(ClientError(message.message_for_child, message.code))

    def _on_socket_error(self, _error: object) -> None:
        # Report an outage once; silent reconnect attempts must not flood the chat.
        if not self._outage_reported:
            self._outage_reported = True
            self.error.emit(ClientError(T.NET_CONNECTION_LOST, "socket"))
        self._schedule_reconnect()

    def _on_socket_disconnected(self) -> None:
        # A question that could not be delivered is dropped; the child already saw the error.
        self._pending_message = None
        self._schedule_reconnect()

    def cancel(self) -> None:
        self._pending_message = None
        self._closing = True
        self._reconnect_timer.stop()
        self.socket.close()
