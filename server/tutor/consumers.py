"""Tutor stream: ``WS /api/v1/sessions/<id>/stream``.

The app sends a ``StudentMessage``; the server answers with ``StreamChunk`` pieces (already
filtered by the harness) and then one ``LearningResponse`` or ``ErrorMessage``. A synchronous
consumer is enough: every child has its own connection, and Channels runs it in a thread.
"""

from __future__ import annotations

import logging

from channels.generic.websocket import WebsocketConsumer
from django.conf import settings
from django.utils import timezone
from learnharness_protocol import ErrorMessage, StreamChunk, StudentMessage
from pydantic import BaseModel, ValidationError

from children.models import ApiClient, hash_token

from .engine import Tutor
from .models import TutorSession

LOG = logging.getLogger(__name__)
MAX_MESSAGE_BYTES = 256 * 1024


def _token(scope: dict) -> str:
    for name, value in scope.get("headers", []):
        if name.lower() == b"authorization":
            scheme, _, token = value.decode("latin-1").partition(" ")
            if scheme.lower() == "bearer":
                return token.strip()
    return ""


class TutorStreamConsumer(WebsocketConsumer):
    session: TutorSession | None = None

    def connect(self) -> None:
        token = _token(self.scope)
        client = (
            ApiClient.objects.filter(token_hash=hash_token(token), active=True).first()
            if token
            else None
        )
        if client is None and settings.TUTOR_REQUIRE_TOKEN:
            self.close(code=4401)
            return
        session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.session = TutorSession.objects.select_related("child").filter(pk=session_id).first()
        if self.session is None:
            self.close(code=4404)
            return
        if client is not None:
            ApiClient.objects.filter(pk=client.pk).update(last_used_at=timezone.now())
        self.accept()

    def _send(self, model: BaseModel) -> None:
        self.send(text_data=model.model_dump_json())

    def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        if self.session is None:
            return
        if not text_data or len(text_data.encode("utf-8")) > MAX_MESSAGE_BYTES:
            self._send(
                ErrorMessage(code="too_large", message_for_child="Die Nachricht ist zu groß.")
            )
            return
        try:
            message = StudentMessage.model_validate_json(text_data)
        except ValidationError:
            self._send(
                ErrorMessage(
                    code="invalid_message", message_for_child="Die Nachricht war ungültig."
                )
            )
            return
        if message.session_id != self.session.id:
            self._send(ErrorMessage(code="wrong_session", message_for_child="Falsche Lernsitzung."))
            return
        result = Tutor(self.session).handle(
            message, on_chunk=lambda text: self._send(StreamChunk(text=text))
        )
        self._send(result)
