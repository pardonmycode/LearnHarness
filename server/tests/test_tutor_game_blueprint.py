"""Games get a skeleton and architecture in the prompt; other projects do not."""

from __future__ import annotations

import pytest
from learnharness_protocol import LearningResponse, StudentMessage
from tutor_helpers import ScriptedProvider

from tutor import engine, harness
from tutor.models import AiSettings, TutorSession

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "idea",
    [
        "Ein Spiel mit einem Fuchs",
        "Mein Rennspiel",
        "ein Jump and Run",
        "Snake im Terminal",
        "Die Spielfigur sammelt Münzen",
        "A small GAME",
    ],
)
def test_python_game_ideas_are_recognised(idea: str) -> None:
    assert harness.is_game_project("python", idea)


@pytest.mark.parametrize(
    "idea",
    [
        "Ein Rechner, zum Beispiel für Brüche",
        "Ein Programm, das Musik abspielt",
        "Meine Schwester soll Klavier spielen lernen",
        "Ein Vokabeltrainer",
        "",
        None,
    ],
)
def test_other_python_ideas_are_no_games(idea: str | None) -> None:
    assert not harness.is_game_project("python", idea)


def test_godot_projects_are_always_games() -> None:
    assert harness.is_game_project("gdscript", None)


def test_blueprint_matches_the_language_and_keeps_the_rules() -> None:
    settings = AiSettings.load()
    godot = harness.system_prompt("mission", settings, game=True)
    python = harness.system_prompt("learn", settings, language="python", game=True)
    assert "Call down, signal up" in godot and "game.py" not in godot
    assert "Eingabe, Aktualisieren, Zeichnen" in python and "move_and_slide" not in python
    assert "Zeige das Grundgerüst nie als Ganzes" in python
    assert python.index("Feste Regeln") < python.index("Grundgerüst für ein Python-Spiel")


def test_no_blueprint_without_a_game_or_for_explanations() -> None:
    settings = AiSettings.load()
    assert "Grundgerüst" not in harness.system_prompt("learn", settings, language="python")
    assert "Grundgerüst" not in harness.system_prompt("explain", settings, game=True)
    assert "Grundgerüst" not in harness.system_prompt("project_plan", settings, game=True)


def test_game_idea_reaches_the_ai_call(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    scripted["provider"] = ScriptedProvider(
        json_answers=[
            {
                "title": "Held",
                "goal": "Held bauen",
                "message": "Los",
                "skill": "variables",
                "steps": [
                    {"title": "Verstehen", "kind": "understand"},
                    {"title": "Bauen", "kind": "exercise"},
                    {"title": "Probieren", "kind": "try"},
                ],
            }
        ]
    )
    message = StudentMessage(
        intent="mission",
        language="python",
        session_id=session.id,
        project_id="spiel",
        project_description="Ein Spiel mit einem Fuchs",
        message="Ein Spiel mit einem Fuchs",
    )
    response = engine.Tutor(session).handle(message)
    assert isinstance(response, LearningResponse)
    assert "Grundgerüst für ein Python-Spiel" in scripted["provider"].calls[0][0]


def test_blueprint_contains_a_folder_structure_for_each_language() -> None:
    godot = harness.game_blueprint("mission", "gdscript")
    python = harness.game_blueprint("mission", "python")
    for folder in ("entities/", "components/", "autoload/", "levels/", "assets/"):
        assert folder in godot
    for folder in ("game/", "states/", "entities/", "systems/"):
        assert folder in python
    assert "Godot-Dateisystem verschieben" in godot
    assert "from game.entities.player import Player" in python
    assert "pyproject.toml" not in python and "tests/" not in python
