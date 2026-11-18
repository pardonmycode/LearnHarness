"""Missions maintained by teachers, the progress history and the CSV/print exports."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone
from learnharness_protocol import Mission, MissionList, ProgressUpdate, Skill, SkillLevel

from children.models import (
    ApiClient,
    Child,
    LearningGroup,
    LearningMission,
    LearningMissionStep,
    ProgressEvent,
)

pytestmark = pytest.mark.django_db


def _headers(token: str) -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def app_token() -> str:
    return ApiClient.issue("PC Raum 12")[1]


@pytest.fixture
def server_token() -> str:
    return ApiClient.issue("Lernserver", ApiClient.Kind.LEARNSERVER)[1]


@pytest.fixture
def teacher_client(client: Client) -> Client:
    User.objects.create_superuser("lehrkraft", password="sehr-geheim-123")
    client.login(username="lehrkraft", password="sehr-geheim-123")
    return client


def _mission(mission_id: str, *groups: LearningGroup, active: bool = True) -> LearningMission:
    mission = LearningMission.objects.create(
        mission_id=mission_id, title=mission_id.title(), goal="Baue etwas!", active=active
    )
    mission.groups.set(groups)
    LearningMissionStep.objects.create(
        mission=mission,
        step_id="verstehen",
        title="Verstehen",
        kind="understand",
        position=1,
        note="Erkläre is_on_floor()",
    )
    LearningMissionStep.objects.create(
        mission=mission, step_id="ausprobieren", title="Testen", kind="try", position=2
    )
    return mission


def test_child_gets_missions_for_everyone_and_its_group(client: Client, app_token: str) -> None:
    blue = LearningGroup.objects.create(name="Blau")
    red = LearningGroup.objects.create(name="Rot")
    _mission("alle")
    _mission("blau", blue)
    _mission("blau-und-rot", blue, red)
    _mission("rot", red)
    _mission("alt", active=False)
    child = Child.objects.create(pseudonym="Fuchs", group=blue)
    loner = Child.objects.create(pseudonym="Eule")

    response = client.get(f"/api/v1/children/{child.pk}/missions/", **_headers(app_token))
    listing = MissionList.model_validate(response.json())
    assert sorted(m.id for m in listing.missions) == ["alle", "blau", "blau-und-rot"]
    first = next(m for m in listing.missions if m.id == "blau")
    assert [s.id for s in first.steps] == ["verstehen", "ausprobieren"]
    assert all(step.note is None for step in first.steps)  # notes are for the learning server

    response = client.get(f"/api/v1/children/{loner.pk}/missions/", **_headers(app_token))
    assert [m.id for m in MissionList.model_validate(response.json()).missions] == ["alle"]


def test_mission_done_is_recorded_once(client: Client, app_token: str) -> None:
    _mission("doppelsprung")
    child = Child.objects.create(pseudonym="Fuchs")
    url = f"/api/v1/children/{child.pk}/missions/doppelsprung/done/"
    for _ in range(2):
        response = client.post(url, **_headers(app_token))
        assert response.status_code == 200
        assert MissionList.model_validate(response.json()).completed == ["doppelsprung"]
    assert child.events.filter(kind="mission").count() == 1

    unknown = client.post(
        f"/api/v1/children/{child.pk}/missions/gibt-es-nicht/done/", **_headers(app_token)
    )
    assert unknown.status_code == 404
    assert unknown.json()["code"] == "unknown_mission"


def test_learning_server_reads_missions_with_notes(
    client: Client, app_token: str, server_token: str
) -> None:
    _mission("doppelsprung")
    assert client.get("/api/v1/missions/", **_headers(app_token)).status_code == 403
    listing = MissionList.model_validate(
        client.get("/api/v1/missions/", **_headers(server_token)).json()
    )
    assert listing.missions[0].steps[0].note == "Erkläre is_on_floor()"
    detail = Mission.model_validate(
        client.get("/api/v1/missions/doppelsprung/", **_headers(server_token)).json()
    )
    assert detail.id == "doppelsprung"
    assert client.get("/api/v1/missions/nein/", **_headers(server_token)).status_code == 404


def test_history_records_only_changes(client: Client, server_token: str) -> None:
    child = Child.objects.create(pseudonym="Fuchs")
    url = f"/api/v1/children/{child.pk}/progress/"

    def put(level: SkillLevel) -> None:
        body = ProgressUpdate(skills=[Skill(id="if", label="Bedingungen", level=level)])
        response = client.put(
            url,
            body.model_dump_json(),
            content_type="application/json",
            **_headers(server_token),
        )
        assert response.status_code == 200

    put(SkillLevel.WITH_HELP)
    put(SkillLevel.WITH_HELP)  # unchanged: no new entry
    put(SkillLevel.CONFIDENT)
    skill_values = list(
        child.events.filter(kind="skill")
        .order_by("recorded_at", "pk")
        .values_list("value", flat=True)
    )
    assert skill_values == [1, 3]

    child.unlock(3)
    child.unlock(2)  # never lowers, nothing recorded
    child.max_level = 2  # teacher lowers it in the admin
    child.save()
    levels = list(
        child.events.filter(kind="level")
        .order_by("recorded_at", "pk")
        .values_list("value", flat=True)
    )
    assert levels == [1, 3, 2]

    child.reset_learning()
    assert list(child.events.values_list("kind", "value")) == [("level", 1)]


def test_history_page_and_csv(teacher_client: Client) -> None:
    blue = LearningGroup.objects.create(name="Blau")
    child = Child.objects.create(pseudonym="Fuchs", group=blue)
    child.set_skill("if", "Bedingungen", 1)
    child.set_skill("if", "Bedingungen", 2)
    child.complete_mission(_mission("doppelsprung"))
    old = ProgressEvent.objects.create(
        child=child,
        kind="skill",
        item_id="loops",
        label="Schleifen",
        value=0,
        recorded_at=timezone.now() - timedelta(days=60),
    )

    page = teacher_client.get(f"/uebersicht/kind/{child.pk}/")
    assert page.status_code == 200
    html = page.content.decode()
    assert "Mit Hilfe" in html and "Fast selbstständig" in html
    assert "Doppelsprung" in html and "Schleifen" in html
    assert "window.print()" in html

    since = (timezone.localdate() - timedelta(days=7)).isoformat()
    recent = teacher_client.get(f"/uebersicht/kind/{child.pk}/?von={since}")
    assert (
        "Schleifen"
        not in recent.content.decode().split("Aktueller Stand")[1].split("Abgeschlossene")[0]
    )

    export = teacher_client.get(f"/uebersicht/kind/{child.pk}/verlauf.csv")
    assert export["Content-Type"].startswith("text/csv")
    text = export.content.decode("utf-8-sig")
    lines = text.strip().splitlines()
    assert lines[0] == "Zeitpunkt;Art;Bezeichnung;Stand"
    assert "Schleifen;Noch nicht begonnen" in lines[1]  # oldest first
    assert any("Mission;Doppelsprung;abgeschlossen" in line for line in lines)

    filtered = teacher_client.get(f"/uebersicht/kind/{child.pk}/verlauf.csv?von={since}")
    assert "Schleifen" not in filtered.content.decode("utf-8-sig")
    assert old.pk  # still stored, only filtered out


def test_overview_csv(teacher_client: Client) -> None:
    blue = LearningGroup.objects.create(name="Blau Gruppe")
    child = Child.objects.create(pseudonym="Fuchs", group=blue, max_level=4)
    child.set_skill("if", "Bedingungen", 3)
    Child.objects.create(pseudonym="Eule")

    export = teacher_client.get(f"/uebersicht/{blue.pk}/export.csv")
    assert 'filename="uebersicht-blau-gruppe.csv"' in export["Content-Disposition"]
    lines = export.content.decode("utf-8-sig").strip().splitlines()
    assert lines == [
        "Spitzname;Gruppe;Level;Zuletzt gesehen;Bedingungen",
        "Fuchs;Blau Gruppe;4;;Sicher",
    ]
    everyone = teacher_client.get("/uebersicht/alle/export.csv").content.decode("utf-8-sig")
    assert "Eule" in everyone
    assert teacher_client.get("/uebersicht/quatsch/export.csv").status_code == 404


def test_exports_need_staff(client: Client) -> None:
    child = Child.objects.create(pseudonym="Fuchs")
    for url in (
        f"/uebersicht/kind/{child.pk}/",
        f"/uebersicht/kind/{child.pk}/verlauf.csv",
        "/uebersicht/alle/export.csv",
    ):
        assert client.get(url).status_code == 302


def test_mission_admin_pages(teacher_client: Client) -> None:
    mission = _mission("doppelsprung")
    assert teacher_client.get("/admin/children/learningmission/").status_code == 200
    page = teacher_client.get(f"/admin/children/learningmission/{mission.pk}/change/")
    assert page.status_code == 200
    child = Child.objects.create(pseudonym="Fuchs")
    change = teacher_client.get(f"/admin/children/child/{child.pk}/change/")
    assert f"/uebersicht/kind/{child.pk}/" in change.content.decode()
