"""Asks the administration for access and waits until a teacher approves this PC.

The PC makes its own random token and sends it once; the server keeps only its hash. After
the approval the same token is the device access, so nobody has to copy or type it.
"""

from __future__ import annotations

import secrets
import time

from learnharness_protocol import DeviceRequestCreate, DeviceRequestStatus
from pydantic import ValidationError
from PyQt6.QtCore import QObject, QTimer

from ..qtcompat import signal
from ..texts import T
from .admin_client import AdminClient, AdminResponse

POLL_MS = 2_000
GIVE_UP_SECONDS = 15 * 60  # the server lets a request wait just as long


class DevicePairing(QObject):
    code_ready = signal(str)  # the four digits the teacher compares
    approved = signal(str)  # the token, now a valid device access
    failed = signal(str)  # a sentence for the teacher

    def __init__(self, parent: QObject | None = None, *, poll_ms: int = POLL_MS) -> None:
        super().__init__(parent)  # type: ignore[arg-type]  # see qtcompat
        self.client: AdminClient | None = None
        self.request_id = ""
        self._started = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(poll_ms)
        self._timer.timeout.connect(self._poll)

    @property
    def waiting(self) -> bool:
        return self.client is not None

    def start(self, url: str, name: str) -> None:
        self.cancel()
        try:
            body = DeviceRequestCreate(name=name, token=secrets.token_urlsafe(32))
        except ValidationError:
            self.failed.emit(T.ADMIN_PAIR_NAME)
            return
        self.client = AdminClient(url, body.token, self)
        self._started = time.monotonic()
        self.client.request("POST", "/devices/requests/", body, self._created)

    def cancel(self) -> None:
        self._timer.stop()
        if self.client is not None:
            self.client.deleteLater()
        self.client, self.request_id = None, ""

    def _status(self, response: AdminResponse) -> DeviceRequestStatus | None:
        try:
            return DeviceRequestStatus.model_validate(response.data) if response.ok else None
        except ValidationError:
            return None

    def _created(self, response: AdminResponse) -> None:
        status = self._status(response)
        if status is None:
            self._fail(T.ADMIN_PAIR_FULL if response.status == 429 else T.ADMIN_PAIR_OFFLINE)
            return
        self.request_id = status.request_id
        self.code_ready.emit(status.code)
        self._timer.start()

    def _poll(self) -> None:
        if self.client is None:
            return
        if time.monotonic() - self._started > GIVE_UP_SECONDS:
            self._fail(T.ADMIN_PAIR_EXPIRED)
            return
        self.client.request("GET", f"/devices/requests/{self.request_id}/", None, self._polled)

    def _polled(self, response: AdminResponse) -> None:
        status = self._status(response)
        if status is None or status.status == "pending" or self.client is None:
            return  # a short network gap: ask again at the next tick
        if status.status == "approved":
            token = self.client.token
            self.cancel()
            self.approved.emit(token)
        else:
            self._fail(
                T.ADMIN_PAIR_REJECTED if status.status == "rejected" else T.ADMIN_PAIR_EXPIRED
            )

    def _fail(self, text: str) -> None:
        self.cancel()
        self.failed.emit(text)
