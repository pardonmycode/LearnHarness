"""HTTP client for the central administration (Django server in server/).

The administration is optional. Every call has a short timeout and failures never block
learning: the app keeps working with the profiles stored on this PC.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import quote

from learnharness_protocol import ProgressUpdate
from pydantic import BaseModel, ValidationError
from PyQt6.QtCore import QByteArray, QEventLoop, QObject, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from ..qtcompat import signal

LOG = logging.getLogger(__name__)
MAX_RESPONSE_BYTES = 1024 * 1024


@dataclass(frozen=True, slots=True)
class AdminResponse:
    status: int  # 0 = not reachable
    data: dict[str, object] | None = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300 and self.data is not None


class AdminClient(QObject):
    progress_received = signal(object)

    def __init__(
        self,
        base_url: str,
        token: str,
        parent: QObject | None = None,
        *,
        timeout_ms: int = 4_000,
    ) -> None:
        super().__init__(parent)  # type: ignore[arg-type]  # see qtcompat
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_ms = timeout_ms
        self.network = QNetworkAccessManager(self)

    @staticmethod
    def child_path(profile_id: str, suffix: str = "") -> str:
        return f"/children/{quote(profile_id, safe='')}/{suffix}"

    def _send(self, method: str, path: str, body: BaseModel | None) -> QNetworkReply:
        request = QNetworkRequest(QUrl(f"{self.base_url}/api/v1{path}"))
        request.setRawHeader(b"Authorization", f"Bearer {self.token}".encode())
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setTransferTimeout(self.timeout_ms)
        if method == "GET":
            reply = self.network.get(request)
        else:
            payload = body.model_dump_json().encode("utf-8") if body is not None else b"{}"
            reply = self.network.sendCustomRequest(request, method.encode(), QByteArray(payload))
        assert reply is not None
        return reply

    @staticmethod
    def _read(reply: QNetworkReply) -> AdminResponse:
        try:
            status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            if not isinstance(status, int):
                LOG.info("Administration not reachable: %s", reply.error().name)
                return AdminResponse(0)
            raw = bytes(reply.readAll())
            if len(raw) > MAX_RESPONSE_BYTES:
                return AdminResponse(status)
            data = json.loads(raw.decode("utf-8")) if raw else None
            return AdminResponse(status, data if isinstance(data, dict) else None)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return AdminResponse(0)
        finally:
            reply.deleteLater()

    def request_blocking(
        self, method: str, path: str, body: BaseModel | None = None
    ) -> AdminResponse:
        """Wait for the answer while Qt keeps running; only used once at start-up."""
        reply = self._send(method, path, body)
        loop = QEventLoop()
        reply.finished.connect(loop.quit)
        if not reply.isFinished():
            loop.exec()
        return self._read(reply)

    def request(
        self,
        method: str,
        path: str,
        body: BaseModel | None = None,
        on_done: Callable[[AdminResponse], None] | None = None,
    ) -> None:
        reply = self._send(method, path, body)

        def finished() -> None:
            response = self._read(reply)
            if on_done is not None:
                on_done(response)

        reply.finished.connect(finished)

    def fetch_progress(self, profile_id: str) -> None:
        def done(response: AdminResponse) -> None:
            if not response.ok:
                return
            try:
                self.progress_received.emit(ProgressUpdate.model_validate(response.data))
            except ValidationError:
                LOG.warning("Ignored invalid progress from the administration")

        self.request("GET", self.child_path(profile_id, "progress/"), on_done=done)
