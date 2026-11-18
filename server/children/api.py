"""JSON API for the learning app and the AI learning server.

Every request needs ``Authorization: Bearer <token>`` (create tokens with
``manage.py create_api_token``). Request and response bodies are the Pydantic models
from ``learnharness_protocol``, so the client validates exactly the same contract.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from learnharness_protocol import (
    ChildProfile,
    ChildProfileList,
    ChildProfileUpdate,
    ErrorMessage,
    LevelUnlock,
    MissionList,
    ProgressUpdate,
)
from pydantic import BaseModel, ValidationError

from .models import ApiClient, Child, LearningGroup, LearningMission, hash_token

Kind = ApiClient.Kind
ALL_KINDS = frozenset({Kind.CLIENT, Kind.LEARNSERVER})
View = Callable[..., JsonResponse]


def _json(model: BaseModel, status: int = 200) -> JsonResponse:
    return JsonResponse(model.model_dump(mode="json"), status=status)


def _error(status: int, code: str, message: str) -> JsonResponse:
    return _json(ErrorMessage(code=code, message_for_child=message), status)


def _authenticate(request: HttpRequest) -> ApiClient | None:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    client = ApiClient.objects.filter(token_hash=hash_token(token.strip()), active=True).first()
    if client is not None:
        ApiClient.objects.filter(pk=client.pk).update(last_used_at=timezone.now())
    return client


def api_view(methods: set[str], kinds: frozenset[str] = ALL_KINDS) -> Callable[[View], View]:
    def decorator(view: View) -> View:
        @csrf_exempt
        @wraps(view)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
            if request.method not in methods:
                return _error(405, "method_not_allowed", "Diese Aktion gibt es hier nicht.")
            client = _authenticate(request)
            if client is None:
                return _error(401, "unauthorized", "Die App ist nicht beim Server angemeldet.")
            if client.kind not in kinds:
                return _error(403, "forbidden", "Das darf diese App nicht.")
            try:
                return view(request, client, *args, **kwargs)
            except ValidationError:
                return _error(400, "invalid_request", "Die Anfrage war nicht gültig.")
            except Child.DoesNotExist:
                return _error(404, "unknown_child", "Dieses Profil gibt es auf dem Server nicht.")
            except LearningMission.DoesNotExist:
                return _error(404, "unknown_mission", "Diese Mission gibt es nicht (mehr).")

        return wrapper

    return decorator


def _active_child(profile_id: str) -> Child:
    return Child.objects.select_related("group").get(pk=profile_id, active=True)


@api_view({"GET", "POST"})
def children(request: HttpRequest, client: ApiClient) -> JsonResponse:
    if request.method == "GET":
        queryset = Child.objects.filter(active=True).select_related("group")
        group = request.GET.get("group")
        if group:
            queryset = queryset.filter(group__name=group)
        return _json(ChildProfileList(profiles=[child.to_protocol() for child in queryset]))

    profile = ChildProfile.model_validate_json(request.body)
    with transaction.atomic():
        existing = Child.objects.select_for_update().filter(pk=profile.profile_id).first()
        if existing is not None:
            if not existing.active:
                return _error(409, "archived", "Dieses Profil wurde von der Lehrkraft archiviert.")
            # Idempotent: a client may register the same local profile twice.
            return _json(existing.to_protocol())
        group = LearningGroup.objects.filter(name=profile.group).first() if profile.group else None
        child = Child.objects.create(
            profile_id=profile.profile_id,
            pseudonym=profile.pseudonym,
            experience_level=profile.experience_level,
            # Keeps the level a child already reached in a purely local profile.
            max_level=profile.max_level,
            group=group,
            last_seen_at=timezone.now(),
        )
    return _json(child.to_protocol(), 201)


@api_view({"GET", "PATCH"})
def child_detail(request: HttpRequest, client: ApiClient, profile_id: str) -> JsonResponse:
    child = _active_child(profile_id)
    if request.method == "PATCH":
        update = ChildProfileUpdate.model_validate_json(request.body)
        if update.pseudonym is not None:
            child.pseudonym = update.pseudonym
        if update.experience_level is not None:
            child.experience_level = update.experience_level
        child.save()
    child.touch()
    return _json(child.to_protocol())


@api_view({"POST"})
def child_unlock(request: HttpRequest, client: ApiClient, profile_id: str) -> JsonResponse:
    unlock = LevelUnlock.model_validate_json(request.body)
    child = _active_child(profile_id)
    child.unlock(unlock.level)
    return _json(child.to_protocol())


@api_view({"GET", "PUT"})
def child_progress(request: HttpRequest, client: ApiClient, profile_id: str) -> JsonResponse:
    child = _active_child(profile_id)
    if request.method == "PUT":
        if client.kind != Kind.LEARNSERVER:
            return _error(403, "forbidden", "Nur der Lernserver trägt Fortschritt ein.")
        update = ProgressUpdate.model_validate_json(request.body)
        with transaction.atomic():
            for skill in update.skills:
                child.set_skill(skill.id, skill.label, int(skill.level))
    return _json(child.progress())


@api_view({"GET"})
def child_missions(request: HttpRequest, client: ApiClient, profile_id: str) -> JsonResponse:
    """Missions assigned to this child's group (or to everyone), without teacher notes."""
    return _json(_active_child(profile_id).missions())


@api_view({"POST"})
def child_mission_done(
    request: HttpRequest, client: ApiClient, profile_id: str, mission_id: str
) -> JsonResponse:
    """Idempotent: the app may report the same finished mission again after being offline."""
    child = _active_child(profile_id)
    mission = LearningMission.objects.get(mission_id=mission_id)
    child.complete_mission(mission)
    return _json(child.missions())


def _all_missions() -> list[LearningMission]:
    return list(LearningMission.objects.filter(active=True).prefetch_related("steps"))


@api_view({"GET"}, frozenset({Kind.LEARNSERVER}))
def missions(request: HttpRequest, client: ApiClient) -> JsonResponse:
    """For the learning server: every active mission including the teacher's notes."""
    return _json(
        MissionList(missions=[mission.to_protocol(with_notes=True) for mission in _all_missions()])
    )


@api_view({"GET"}, frozenset({Kind.LEARNSERVER}))
def mission_detail(request: HttpRequest, client: ApiClient, mission_id: str) -> JsonResponse:
    mission = LearningMission.objects.prefetch_related("steps").get(mission_id=mission_id)
    return _json(mission.to_protocol(with_notes=True))
