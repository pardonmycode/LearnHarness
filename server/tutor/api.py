"""HTTP part of the learning-server protocol (``/api/v1``); the tutor stream is in consumers.py.

The app sends its device token (the same as for the administration). Without
``TUTOR_REQUIRE_TOKEN=0`` requests without a valid token are rejected, so nobody else on the
network can use the (possibly paid) AI.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from learnharness_protocol import (
    CodeSubmission,
    ErrorMessage,
    HealthStatus,
    HintRequest,
    ProgressUpdate,
    SessionCreate,
    SessionInfo,
    Submission,
)
from pydantic import BaseModel, ValidationError

from children.api import _authenticate
from children.models import ApiClient, Child

from .engine import TASKS, Tutor
from .models import TutorSession
from .providers import model_available

View = Callable[..., JsonResponse]


def _json(model: BaseModel, status: int = 200) -> JsonResponse:
    return JsonResponse(model.model_dump(mode="json"), status=status)


def _error(status: int, code: str, message: str) -> JsonResponse:
    return _json(ErrorMessage(code=code, message_for_child=message), status)


def _status(error: ErrorMessage) -> int:
    return {"rate_limited": 429, "model_unavailable": 503}.get(error.code, 400)


def tutor_client(request: HttpRequest) -> tuple[bool, ApiClient | None]:
    client = _authenticate(request)
    return (client is not None or not settings.TUTOR_REQUIRE_TOKEN), client


def tutor_view(methods: set[str]) -> Callable[[View], View]:
    def decorator(view: View) -> View:
        @csrf_exempt
        @wraps(view)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
            if request.method not in methods:
                return _error(405, "method_not_allowed", "Diese Aktion gibt es hier nicht.")
            allowed, client = tutor_client(request)
            if not allowed:
                return _error(401, "unauthorized", "Die App ist nicht beim Server angemeldet.")
            try:
                return view(request, client, *args, **kwargs)
            except ValidationError:
                return _error(400, "invalid_request", "Die Anfrage war nicht gültig.")
            except TutorSession.DoesNotExist:
                return _error(404, "unknown_session", "Die Lernsitzung ist abgelaufen.")

        return wrapper

    return decorator


@csrf_exempt
def health(request: HttpRequest) -> JsonResponse:
    # No token needed: the app shows the connection status before anything else.
    ok, latency = model_available()
    return _json(HealthStatus(server_ok=True, model_ok=ok, latency_ms=latency))


@tutor_view({"POST"})
def sessions(request: HttpRequest, client: ApiClient | None) -> JsonResponse:
    data = SessionCreate.model_validate_json(request.body)
    child = Child.objects.filter(pk=data.student_profile_id, active=True).first()
    if child is not None:
        child.touch()
    session = TutorSession.objects.create(
        child=child,
        profile_id=data.student_profile_id,
        pseudonym=data.student_pseudonym,
        experience_level=data.experience_level,
        project_id=data.project_id[:200],
        api_client=client,
    )
    return _json(
        SessionInfo(
            session_id=session.id,
            student_pseudonym=session.pseudonym,
            current_task_id="move_player_right",
        ),
        201,
    )


def _session(session_id: str) -> TutorSession:
    session = TutorSession.objects.select_related("child").get(pk=session_id)
    TutorSession.objects.filter(pk=session.pk).update(last_activity=timezone.now())
    return session


@tutor_view({"POST"})
def hints(request: HttpRequest, client: ApiClient | None, session_id: str) -> JsonResponse:
    request_data = HintRequest.model_validate_json(request.body)
    result = Tutor(_session(session_id)).hint(request_data.task_id)
    return _json(result, _status(result) if isinstance(result, ErrorMessage) else 200)


@tutor_view({"GET"})
def task_detail(request: HttpRequest, client: ApiClient | None, task_id: str) -> JsonResponse:
    task = TASKS.get(task_id)
    if task is None:
        return _error(404, "unknown_task", "Diese Aufgabe kenne ich nicht.")
    return _json(task)


@tutor_view({"POST"})
def exercise_submission(
    request: HttpRequest, client: ApiClient | None, exercise_id: str
) -> JsonResponse:
    submission = Submission.model_validate_json(request.body)
    if submission.exercise_id != exercise_id or not submission.session_id:
        return _error(400, "invalid_request", "Die Anfrage war nicht gültig.")
    result = Tutor(_session(submission.session_id)).review_submission(submission)
    status = 404 if isinstance(result, ErrorMessage) else 200
    return _json(result, status)


@tutor_view({"POST"})
def code_submission(request: HttpRequest, client: ApiClient | None, task_id: str) -> JsonResponse:
    submission = CodeSubmission.model_validate_json(request.body)
    if submission.task_id != task_id:
        return _error(400, "invalid_request", "Die Anfrage war nicht gültig.")
    result = Tutor(_session(submission.session_id)).review_code(submission)
    return _json(result, _status(result) if isinstance(result, ErrorMessage) else 200)


@tutor_view({"GET"})
def progress(request: HttpRequest, client: ApiClient | None) -> JsonResponse:
    session_id = request.GET.get("session_id", "")
    session = TutorSession.objects.select_related("child").filter(pk=session_id).first()
    if session is None or session.child is None:
        return _json(ProgressUpdate())
    return _json(session.child.progress())
