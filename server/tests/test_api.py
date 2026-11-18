"""API contract tests: bodies are validated with the shared protocol models."""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.core.management import call_command
from django.test import Client
from learnharness_protocol import ChildProfile, ChildProfileList, ErrorMessage, ProgressUpdate

from children.models import ApiClient, Child, LearningGroup, SkillProgress

pytestmark = pytest.mark.django_db


def _headers(token: str) -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def app_token() -> str:
    return ApiClient.issue("PC Raum 12")[1]


@pytest.fixture
def server_token() -> str:
    return ApiClient.issue("Lernserver", ApiClient.Kind.LEARNSERVER)[1]


def _profile(pseudonym: str = "Fuchs", **extra: object) -> dict[str, object]:
    return ChildProfile(
        profile_id=uuid4().hex, pseudonym=pseudonym, experience_level=1, **extra
    ).model_dump(mode="json")


def test_requests_without_valid_token_are_rejected(client: Client) -> None:
    assert client.get("/api/v1/children/").status_code == 401
    response = client.get("/api/v1/children/", **_headers("falsch"))
    assert response.status_code == 401
    ErrorMessage.model_validate(response.json())


def test_inactive_token_is_rejected(client: Client, app_token: str) -> None:
    ApiClient.objects.update(active=False)
    assert client.get("/api/v1/children/", **_headers(app_token)).status_code == 401


def test_token_is_stored_hashed(app_token: str) -> None:
    assert not ApiClient.objects.filter(token_hash=app_token).exists()


def test_register_list_and_update_child(client: Client, app_token: str) -> None:
    body = _profile(max_level=3)
    created = client.post(
        "/api/v1/children/", body, content_type="application/json", **_headers(app_token)
    )
    assert created.status_code == 201
    assert ChildProfile.model_validate(created.json()).max_level == 3

    # Registering again is idempotent.
    again = client.post(
        "/api/v1/children/", body, content_type="application/json", **_headers(app_token)
    )
    assert again.status_code == 200

    listing = ChildProfileList.model_validate(
        client.get("/api/v1/children/", **_headers(app_token)).json()
    )
    assert [p.pseudonym for p in listing.profiles] == ["Fuchs"]

    url = f"/api/v1/children/{body['profile_id']}/"
    patched = client.patch(
        url,
        {"pseudonym": "  Roter   Fuchs "},
        content_type="application/json",
        **_headers(app_token),
    )
    assert patched.status_code == 200
    assert patched.json()["pseudonym"] == "Roter Fuchs"
    assert Child.objects.get().last_seen_at is not None


def test_invalid_bodies_are_rejected(client: Client, app_token: str) -> None:
    bad = _profile()
    bad["pseudonym"] = "x"
    response = client.post(
        "/api/v1/children/", bad, content_type="application/json", **_headers(app_token)
    )
    assert response.status_code == 400
    response = client.post(
        "/api/v1/children/", "kein json", content_type="application/json", **_headers(app_token)
    )
    assert response.status_code == 400


def test_group_filter_and_archived_children(client: Client, app_token: str) -> None:
    group = LearningGroup.objects.create(name="AG Montag")
    Child.objects.create(pseudonym="Eule", group=group)
    Child.objects.create(pseudonym="Igel")
    archived = Child.objects.create(pseudonym="Biber", active=False)

    listing = client.get("/api/v1/children/?group=AG Montag", **_headers(app_token)).json()
    assert [p["pseudonym"] for p in listing["profiles"]] == ["Eule"]
    assert listing["profiles"][0]["group"] == "AG Montag"

    detail = client.get(f"/api/v1/children/{archived.pk}/", **_headers(app_token))
    assert detail.status_code == 404
    body = archived.to_protocol().model_dump(mode="json")
    response = client.post(
        "/api/v1/children/", body, content_type="application/json", **_headers(app_token)
    )
    assert response.status_code == 409


def test_clients_can_only_raise_the_level(client: Client, app_token: str) -> None:
    child = Child.objects.create(pseudonym="Luchs", max_level=4)
    url = f"/api/v1/children/{child.pk}/unlock/"
    lower = client.post(url, {"level": 2}, content_type="application/json", **_headers(app_token))
    assert lower.json()["max_level"] == 4
    higher = client.post(url, {"level": 6}, content_type="application/json", **_headers(app_token))
    assert higher.json()["max_level"] == 6
    too_high = client.post(
        url, {"level": 11}, content_type="application/json", **_headers(app_token)
    )
    assert too_high.status_code == 400


def test_only_learnserver_writes_progress(
    client: Client, app_token: str, server_token: str
) -> None:
    child = Child.objects.create(pseudonym="Otter")
    url = f"/api/v1/children/{child.pk}/progress/"
    update = {
        "type": "progress_update",
        "skills": [
            {"id": "variables", "label": "Variablen", "level": 2},
            {"id": "loops", "label": "Schleifen", "level": 1},
        ],
    }
    denied = client.put(url, update, content_type="application/json", **_headers(app_token))
    assert denied.status_code == 403

    written = client.put(url, update, content_type="application/json", **_headers(server_token))
    assert written.status_code == 200
    update["skills"][0]["level"] = 3  # type: ignore[index]
    client.put(url, update, content_type="application/json", **_headers(server_token))
    assert SkillProgress.objects.count() == 2

    progress = ProgressUpdate.model_validate(client.get(url, **_headers(app_token)).json())
    assert {skill.id: int(skill.level) for skill in progress.skills} == {
        "variables": 3,
        "loops": 1,
    }


def test_wrong_method_and_unknown_child(client: Client, app_token: str) -> None:
    assert client.delete("/api/v1/children/", **_headers(app_token)).status_code == 405
    missing = client.get(f"/api/v1/children/{uuid4().hex}/", **_headers(app_token))
    assert missing.status_code == 404


def test_reset_learning_removes_skills() -> None:
    child = Child.objects.create(pseudonym="Dachs", max_level=5)
    SkillProgress.objects.create(child=child, skill_id="if", label="Bedingungen", level=2)
    child.reset_learning()
    child.refresh_from_db()
    assert child.max_level == 1
    assert not child.skills.exists()


def test_create_api_token_command(capsys: pytest.CaptureFixture[str]) -> None:
    call_command("create_api_token", "PC Raum 7", "--kind", "client")
    token = capsys.readouterr().out.strip().splitlines()[-1]
    assert ApiClient.objects.get(name="PC Raum 7").token_hash != token
    assert Client().get("/api/v1/children/", **_headers(token)).status_code == 200
