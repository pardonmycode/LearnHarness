"""A PC asks for access; a teacher approves it under „Wartende Geräte“ without any token typing."""

from __future__ import annotations

import secrets
from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from children.models import ApiClient, DeviceRequest
from children.models.devices import MAX_PENDING_REQUESTS

pytestmark = pytest.mark.django_db
URL = "/api/v1/devices/requests/"


def _ask(client: Client, name: str = "PC 3", token: str | None = None) -> tuple[dict, str]:
    token = token or secrets.token_urlsafe(32)
    response = client.post(URL, {"name": name, "token": token}, content_type="application/json")
    return {"http": response.status_code, **response.json()}, token


def _poll(client: Client, request_id: str, token: str) -> dict:
    response = client.get(f"{URL}{request_id}/", HTTP_AUTHORIZATION=f"Bearer {token}")
    return {"status_code": response.status_code, **response.json()}


def test_pc_asks_and_waits_with_a_code(client: Client) -> None:
    answer, token = _ask(client, "  PC   3 ")
    assert answer["http"] == 200 and answer["status"] == "pending"
    assert answer["code"].isdigit() and len(answer["code"]) == 4
    device = DeviceRequest.objects.get()
    assert device.name == "PC 3" and token not in device.token_hash
    polled = _poll(client, answer["request_id"], token)
    assert polled["status"] == "pending" and polled["code"] == answer["code"]


def test_only_the_asking_pc_sees_the_answer(client: Client) -> None:
    answer, _ = _ask(client)
    assert _poll(client, answer["request_id"], "fremder-token")["status_code"] == 404
    assert client.get(f"{URL}{answer['request_id']}/").status_code == 404


@pytest.mark.parametrize(
    "body",
    [{"name": "x", "token": "a" * 40}, {"name": "PC 1", "token": "kurz"}, {"name": "PC 1"}],
)
def test_invalid_requests_are_refused(client: Client, body: dict) -> None:
    response = client.post(URL, body, content_type="application/json")
    assert response.status_code == 400 and not DeviceRequest.objects.exists()


def test_teacher_approves_and_the_token_works(client: Client, teacher: Client) -> None:
    pc = Client()
    answer, token = _ask(pc)
    assert pc.get("/api/v1/children/", HTTP_AUTHORIZATION=f"Bearer {token}").status_code == 401
    page = teacher.get("/admin/children/devicerequest/").content.decode()
    assert answer["code"] in page and "Genehmigen" in page
    teacher.post(f"/admin/children/devicerequest/{answer['request_id']}/genehmigen/")
    assert _poll(pc, answer["request_id"], token)["status"] == "approved"
    access = ApiClient.objects.get()
    assert access.name == "PC 3" and access.kind == ApiClient.Kind.CLIENT
    assert pc.get("/api/v1/children/", HTTP_AUTHORIZATION=f"Bearer {token}").status_code == 200


def test_same_name_gets_a_number_and_rejected_stays_out(client: Client, teacher: Client) -> None:
    first, _ = _ask(client)
    second, _ = _ask(client)
    third, token = _ask(client)
    for answer in (first, second):
        teacher.post(f"/admin/children/devicerequest/{answer['request_id']}/genehmigen/")
    assert sorted(ApiClient.objects.values_list("name", flat=True)) == ["PC 3", "PC 3 (2)"]
    teacher.post(f"/admin/children/devicerequest/{third['request_id']}/ablehnen/")
    assert _poll(client, third["request_id"], token)["status"] == "rejected"
    teacher.post(f"/admin/children/devicerequest/{third['request_id']}/genehmigen/")
    assert ApiClient.objects.count() == 2


def test_old_requests_expire(client: Client) -> None:
    answer, token = _ask(client)
    DeviceRequest.objects.update(created_at=timezone.now() - timedelta(minutes=16))
    assert _poll(client, answer["request_id"], token)["status"] == "expired"
    assert DeviceRequest.objects.get().approve() is None


def test_buttons_need_a_logged_in_teacher_and_post(client: Client, teacher: Client) -> None:
    answer, _ = _ask(client)
    stranger = Client()
    stranger.post(f"/admin/children/devicerequest/{answer['request_id']}/genehmigen/")
    assert not ApiClient.objects.exists()
    response = teacher.get(f"/admin/children/devicerequest/{answer['request_id']}/genehmigen/")
    assert response.status_code == 405 and not ApiClient.objects.exists()


def test_too_many_waiting_pcs_are_refused(client: Client) -> None:
    for number in range(MAX_PENDING_REQUESTS):
        _ask(client, f"PC {number}")
    answer, _ = _ask(client, "PC zu viel")
    assert answer["http"] == 429


def test_buttons_work_with_csrf_protection(client: Client) -> None:
    from django.contrib.auth.models import User

    answer, _ = _ask(client)
    User.objects.create_superuser("lehrkraft2", password="sehr-geheim-123")
    browser = Client(enforce_csrf_checks=True)
    browser.login(username="lehrkraft2", password="sehr-geheim-123")
    page = browser.get("/admin/children/devicerequest/").content.decode()
    form_start, button = page.index('id="changelist-form"'), page.index("Genehmigen</button>")
    assert form_start < button < page.index("</form>", form_start)  # sends the form's token
    csrf = browser.cookies["csrftoken"].value
    browser.post(
        f"/admin/children/devicerequest/{answer['request_id']}/genehmigen/",
        {"csrfmiddlewaretoken": csrf},
    )
    assert ApiClient.objects.filter(name="PC 3").exists()
