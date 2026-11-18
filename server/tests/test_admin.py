"""Smoke tests for the teacher administration."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from django.test import Client

from children.models import ApiClient, Child, SkillProgress

pytestmark = pytest.mark.django_db


@pytest.fixture
def teacher_client(client: Client) -> Client:
    User.objects.create_superuser("lehrkraft", password="sehr-geheim-123")
    client.login(username="lehrkraft", password="sehr-geheim-123")
    return client


def test_admin_pages_render(teacher_client: Client) -> None:
    child = Child.objects.create(pseudonym="Fuchs")
    SkillProgress.objects.create(child=child, skill_id="if", label="Bedingungen", level=1)
    for url in (
        "/admin/",
        "/admin/children/child/",
        f"/admin/children/child/{child.pk}/change/",
        "/admin/children/learninggroup/add/",
        "/admin/children/apiclient/add/",
    ):
        assert teacher_client.get(url).status_code == 200, url


def test_admin_actions(teacher_client: Client) -> None:
    child = Child.objects.create(pseudonym="Igel", max_level=2)
    SkillProgress.objects.create(child=child, skill_id="if", label="Bedingungen", level=1)
    url = "/admin/children/child/"
    teacher_client.post(url, {"action": "unlock_next_level", "_selected_action": [child.pk]})
    child.refresh_from_db()
    assert child.max_level == 3
    teacher_client.post(url, {"action": "reset_learning", "_selected_action": [child.pk]})
    child.refresh_from_db()
    assert child.max_level == 1 and not child.skills.exists()
    teacher_client.post(url, {"action": "archive", "_selected_action": [child.pk]})
    child.refresh_from_db()
    assert not child.active


def test_new_api_client_shows_token_once(teacher_client: Client) -> None:
    response = teacher_client.post(
        "/admin/children/apiclient/add/",
        {"name": "PC Raum 3", "kind": "client", "active": "on"},
        follow=True,
    )
    shown = [str(message) for message in response.context["messages"]]
    assert any("wird nur jetzt angezeigt" in message for message in shown)
    assert ApiClient.objects.get(name="PC Raum 3").token_hash
