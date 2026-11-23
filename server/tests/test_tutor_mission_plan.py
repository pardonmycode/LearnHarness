"""A mission plan has a clear structure before a child gets to see it."""

from __future__ import annotations

from typing import Any

import pytest

from tutor import harness


def _plan(steps: list[tuple[str, str]], **overrides: Any) -> dict[str, Any]:
    return {
        "title": "Münzen zählen",
        "goal": "Der Fuchs zählt seine Münzen.",
        "skill": "variables",
        "steps": [{"title": title, "kind": kind} for title, kind in steps],
    } | overrides


GOOD = [("Verstehen", "understand"), ("Zähler bauen", "exercise"), ("Starten", "try")]


def test_good_plan_and_missing_try_step_is_added() -> None:
    assert len(harness.check_mission_plan(_plan(GOOD), ["variables"], "Los")) == 3
    steps = harness.check_mission_plan(_plan(GOOD[:2]), ["variables"], "Ausprobieren")
    assert steps[-1] == {"title": "Ausprobieren", "kind": "try"}


@pytest.mark.parametrize(
    "steps",
    [
        [("Verstehen", "understand"), ("Starten", "try")],
        [("Verstehen", "understand"), ("Lernen", "learn"), ("Starten", "try")],
        [("Bauen", "exercise"), ("Starten", "try"), ("Mehr", "exercise"), ("Ende", "try")],
        [("A", "learn"), ("B", "exercise"), ("C", "exercise"), ("D", "learn"), ("E", "exercise")],
        [("Verstehen", "raten"), ("Bauen", "exercise"), ("Starten", "try")],
    ],
)
def test_bad_structure_is_rejected(steps: list[tuple[str, str]]) -> None:
    with pytest.raises(harness.HarnessRejected):
        harness.check_mission_plan(_plan(steps), ["variables"], "Los")


@pytest.mark.parametrize(
    "overrides",
    [
        {"skill": "classes"},
        {"title": ""},
        {"goal": "  "},
        {"title": "leben = 100"},
        {"goal": "Nutze `print`"},
        {"goal": "Rufe springen() auf"},
    ],
)
def test_bad_fields_are_rejected(overrides: dict[str, Any]) -> None:
    with pytest.raises(harness.HarnessRejected):
        harness.check_mission_plan(_plan(GOOD, **overrides), ["variables"], "Los")


def test_german_words_that_look_like_code_are_fine() -> None:
    steps = [("return nutzen", "learn"), ("var anlegen", "exercise"), ("Starten", "try")]
    assert harness.check_mission_plan(_plan(steps), ["variables"], "Los")
