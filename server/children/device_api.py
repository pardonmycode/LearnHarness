"""A PC asks for access without a token; a teacher approves it under „Wartende Geräte“."""

from __future__ import annotations

from django.db import IntegrityError
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from learnharness_protocol import DeviceRequestCreate, DeviceRequestStatus
from pydantic import ValidationError

from .api import _error, _json
from .models import ApiClient, DeviceRequest, hash_token
from .models.devices import MAX_PENDING_REQUESTS, REQUEST_LIFETIME


def _status(request: DeviceRequest) -> JsonResponse:
    return _json(
        DeviceRequestStatus(request_id=request.id, code=request.code, status=request.state)
    )


@csrf_exempt
def create_request(request: HttpRequest) -> JsonResponse:
    """Open to every PC in the network: it only creates an entry a teacher must approve."""
    if request.method != "POST":
        return _error(405, "method_not_allowed", "Diese Aktion gibt es hier nicht.")
    try:
        body = DeviceRequestCreate.model_validate_json(request.body)
    except ValidationError:
        return _error(400, "invalid_request", "Bitte einen kurzen Namen wie „PC 3“ eintragen.")
    open_since = timezone.now() - REQUEST_LIFETIME
    waiting = DeviceRequest.objects.filter(
        status=DeviceRequest.Status.PENDING, created_at__gte=open_since
    )
    if waiting.count() >= MAX_PENDING_REQUESTS:
        return _error(429, "too_many_requests", "Gerade warten zu viele Geräte. Später nochmal.")
    token_hash = hash_token(body.token)
    if ApiClient.objects.filter(token_hash=token_hash).exists():
        return _error(409, "token_taken", "Bitte frage noch einmal neu an.")
    try:
        device = DeviceRequest.objects.create(name=body.name, token_hash=token_hash)
    except IntegrityError:
        return _error(409, "token_taken", "Bitte frage noch einmal neu an.")
    return _status(device)


def request_status(request: HttpRequest, request_id: str) -> JsonResponse:
    """Only the PC that asked may see the answer: it proves this with its own token."""
    if request.method != "GET":
        return _error(405, "method_not_allowed", "Diese Aktion gibt es hier nicht.")
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    device = DeviceRequest.objects.filter(id=request_id).first()
    if (
        device is None
        or scheme.lower() != "bearer"
        or hash_token(token.strip()) != device.token_hash
    ):
        return _error(404, "unknown_request", "Diese Anfrage gibt es nicht (mehr).")
    return _status(device)
