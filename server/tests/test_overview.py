"""Group overview for teachers (/uebersicht/)."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from django.test import Client

from children.models import Child, LearningGroup, SkillProgress

pytestmark = pytest.mark.django_db


@pytest.fixture
def teacher_client(client: Client) -> Client:
    User.objects.create_superuser("lehrkraft", password="sehr-geheim-123")
    client.login(username="lehrkraft", password="sehr-geheim-123")
    return client


@pytest.fixture
def groups() -> tuple[LearningGroup, LearningGroup]:
    blue = LearningGroup.objects.create(name="Blau")
    red = LearningGroup.objects.create(name="Rot")
    fuchs = Child.objects.create(pseudonym="Fuchs", group=blue, max_level=4)
    SkillProgress.objects.create(child=fuchs, skill_id="loops", label="Schleifen", level=3)
    SkillProgress.objects.create(child=fuchs, skill_id="if", label="Bedingungen", level=1)
    igel = Child.objects.create(pseudonym="Igel", group=blue)
    SkillProgress.objects.create(child=igel, skill_id="vars", label="Variablen", level=2)
    dachs = Child.objects.create(pseudonym="Dachs", group=red)
    SkillProgress.objects.create(child=dachs, skill_id="lists", label="Listen", level=0)
    Child.objects.create(pseudonym="Archiviert", group=blue, active=False)
    Child.objects.create(pseudonym="Eule")
    return blue, red


def test_anonymous_and_non_staff_are_redirected_to_login(client: Client) -> None:
    response = client.get("/uebersicht/")
    assert response.status_code == 302
    assert response["Location"].startswith("/admin/login/")
    User.objects.create_user("kind", password="sehr-geheim-123")
    client.login(username="kind", password="sehr-geheim-123")
    assert client.get("/uebersicht/").status_code == 302


def test_overview_shows_skills_levels_and_legend(teacher_client: Client, groups) -> None:
    response = teacher_client.get("/uebersicht/")
    assert response.status_code == 200
    html = response.content.decode()
    for text in ("Fuchs", "Igel", "Dachs", "Eule", "Schleifen", "Bedingungen", "Listen"):
        assert text in html
    assert "Archiviert" not in html
    for css, label in (
        ("lh-level-0", "Noch nicht begonnen"),
        ("lh-level-1", "Mit Hilfe"),
        ("lh-level-2", "Fast selbstständig"),
        ("lh-level-3", "Sicher"),
    ):
        assert css in html and label in html
    assert "Zuletzt gesehen" in html
    columns = [column.label for column in response.context["columns"]]
    assert columns == ["Bedingungen", "Listen", "Schleifen", "Variablen"]
    fuchs = next(row for row in response.context["rows"] if row.child.pseudonym == "Fuchs")
    assert [cell.level if cell else None for cell in fuchs.cells] == [1, None, 3, None]


def test_group_filter(teacher_client: Client, groups) -> None:
    blue, red = groups
    response = teacher_client.get(f"/uebersicht/{blue.pk}/")
    assert response.status_code == 200
    names = [row.child.pseudonym for row in response.context["rows"]]
    assert names == ["Fuchs", "Igel"]
    assert [column.skill_id for column in response.context["columns"]] == ["if", "loops", "vars"]

    response = teacher_client.get("/uebersicht/ohne-gruppe/")
    assert [row.child.pseudonym for row in response.context["rows"]] == ["Eule"]

    assert teacher_client.get("/uebersicht/9999/").status_code == 404


def test_group_selector_redirects_to_clean_url(teacher_client: Client, groups) -> None:
    blue, _ = groups
    response = teacher_client.get("/uebersicht/", {"gruppe": blue.pk})
    assert response.status_code == 302 and response["Location"] == f"/uebersicht/{blue.pk}/"
    response = teacher_client.get("/uebersicht/", {"gruppe": "alle"})
    assert response["Location"] == "/uebersicht/"
    response = teacher_client.get("/uebersicht/", {"gruppe": "../admin"})
    assert response["Location"] == "/uebersicht/"


def test_overview_query_count_does_not_grow_with_children(
    teacher_client: Client, groups, django_assert_max_num_queries
) -> None:
    blue, _ = groups
    for index in range(20):
        child = Child.objects.create(pseudonym=f"Kind {index}", group=blue)
        SkillProgress.objects.create(child=child, skill_id=f"s{index}", label=f"F {index}", level=2)
    with django_assert_max_num_queries(8):
        assert teacher_client.get("/uebersicht/").status_code == 200
    with django_assert_max_num_queries(8):
        assert teacher_client.get(f"/uebersicht/{blue.pk}/").status_code == 200


def test_admin_links_to_overview(teacher_client: Client, groups) -> None:
    blue, _ = groups
    html = teacher_client.get("/admin/children/learninggroup/").content.decode()
    assert f'href="/uebersicht/{blue.pk}/"' in html
    assert 'href="/uebersicht/"' in html
