"""Fixtures shared by the server tests."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from django.test import Client
from learnharness_protocol import SessionInfo
from tutor_helpers import ScriptedProvider, _headers

from children.models import ApiClient, Child
from tutor import engine
from tutor.models import TutorSession


@pytest.fixture
def token() -> str:
    return ApiClient.issue("PC 1")[1]


@pytest.fixture
def scripted(monkeypatch: pytest.MonkeyPatch) -> dict[str, ScriptedProvider]:
    holder: dict[str, ScriptedProvider] = {"provider": ScriptedProvider()}
    monkeypatch.setattr(engine, "get_provider", lambda settings=None: holder["provider"])
    return holder


@pytest.fixture
def session(client: Client, token: str) -> TutorSession:
    child = Child.objects.create(pseudonym="Fuchs")
    response = client.post(
        "/api/v1/sessions",
        {
            "project_id": "spiel",
            "client_version": "0.1",
            "student_profile_id": child.pk,
            "student_pseudonym": "Fuchs",
            "experience_level": 1,
        },
        content_type="application/json",
        **_headers(token),
    )
    assert response.status_code == 201
    info = SessionInfo.model_validate(response.json())
    return TutorSession.objects.get(pk=info.session_id)


@pytest.fixture
def teacher(client: Client) -> Client:
    User.objects.create_superuser("lehrkraft", password="sehr-geheim-123")
    client.login(username="lehrkraft", password="sehr-geheim-123")
    return client
