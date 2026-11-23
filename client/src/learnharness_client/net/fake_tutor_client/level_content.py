"""Offline exercises for the ten LearnAgent levels, in Godot and in Python."""

from __future__ import annotations

from typing import Any

from learnharness_protocol import (
    Blank,
    Choice,
    FillBlanksExercise,
    FindBugExercise,
    MultipleChoiceExercise,
    OrderingExercise,
    OrderItem,
    TextBlank,
    TextBlanksExercise,
)
from learnharness_protocol.exercises import Exercise

FILL_LEVELS = (3, 4)  # the fixed practice rounds are dropdown exercises
_MOVE = ["extends Node2D", "var speed = 200.0", "func _process(delta):"]
_GREET = 'name = input("Wie heißt du? ")'

_GODOT: dict[int, tuple[type, dict[str, Any], dict[str, Any]]] = {
    1: (
        MultipleChoiceExercise,
        {
            "prompt": "Welche Achse bewegt eine Figur nach links und rechts?",
            "choices": [
                Choice(id="x_axis", text="Die X-Achse"),
                Choice(id="y_axis", text="Die Y-Achse"),
            ],
        },
        {"choice": "x_axis"},
    ),
    2: (
        MultipleChoiceExercise,
        {
            "prompt": "Wie bleibt die Bewegung unabhängig von der Bildrate?",
            "choices": [
                Choice(id="use_delta", text="Geschwindigkeit mit delta multiplizieren"),
                Choice(id="fixed_step", text="In jedem Bild immer 10 Pixel addieren"),
            ],
        },
        {"choice": "use_delta"},
    ),
    3: (
        FillBlanksExercise,
        {
            "prompt": "Wähle die waagerechte Achse aus.",
            "code": "position.{{axis}} += 10",
            "blanks": [Blank(id="axis", options=["x", "y"])],
        },
        {"axis": "x"},
    ),
    4: (
        FillBlanksExercise,
        {
            "prompt": "Ergänze Achse und Geschwindigkeit.",
            "code": "position.{{axis}} += {{value}} * delta",
            "blanks": [
                Blank(id="axis", options=["x", "y", "z"]),
                Blank(id="value", options=["position", "speed", "delta"]),
            ],
        },
        {"axis": "x", "value": "speed"},
    ),
    5: (
        OrderingExercise,
        {
            "prompt": "Bringe die Zeilen in die richtige Reihenfolge.",
            "items": [
                OrderItem(id="move", text="\tposition.x += speed * delta"),
                OrderItem(id="extends", text="extends Node2D"),
                OrderItem(id="process", text="func _process(delta):"),
                OrderItem(id="speed", text="var speed = 200.0"),
            ],
        },
        {"order": ["extends", "speed", "process", "move"]},
    ),
    6: (
        TextBlanksExercise,
        {
            "prompt": "Tippe die waagerechte Achse ein.",
            "code": "position.{{axis}} += 10",
            "blanks": [TextBlank(id="axis", placeholder="Achse")],
        },
        {"axis": "x"},
    ),
    7: (
        TextBlanksExercise,
        {
            "prompt": "Tippe die waagerechte Achse und die Variable für das Tempo ein.",
            "code": "position.{{axis}} += {{value}} * delta",
            "blanks": [
                TextBlank(id="axis", placeholder="Achse"),
                TextBlank(id="value", placeholder="Variable"),
            ],
        },
        {"axis": "x", "value": "speed"},
    ),
    8: (
        FindBugExercise,
        {
            "prompt": "Die Figur soll nach rechts laufen. Welche Zeile bewegt sie nach unten?",
            "lines": [*_MOVE, "\tposition.y += speed * delta"],
        },
        {"lines": [4]},
    ),
    9: (
        FindBugExercise,
        {
            "prompt": "Die Figur soll nach rechts laufen, läuft aber nach links. Wo liegt es?",
            "lines": [*_MOVE, "\tposition.x -= speed * delta"],
        },
        {"lines": [4]},
    ),
    10: (
        FindBugExercise,
        {
            "prompt": "Auf schnellen Computern rennt die Figur viel zu schnell. Wo liegt es?",
            "lines": [*_MOVE, "\tposition.x += speed"],
        },
        {"lines": [4]},
    ),
}

_PYTHON: dict[int, tuple[type, dict[str, Any], dict[str, Any]]] = {
    1: (
        MultipleChoiceExercise,
        {
            "prompt": "Welcher Befehl zeigt Text auf dem Bildschirm an?",
            "choices": [Choice(id="right", text="print"), Choice(id="wrong", text="input")],
        },
        {"choice": "right"},
    ),
    2: (
        MultipleChoiceExercise,
        {
            "prompt": "Wie schreibst du in Python einen Text?",
            "choices": [
                Choice(id="right", text="In Anführungszeichen"),
                Choice(id="wrong", text="Ohne Zeichen drumherum"),
            ],
        },
        {"choice": "right"},
    ),
    3: (
        FillBlanksExercise,
        {
            "prompt": "Wähle den Befehl, der Text anzeigt.",
            "code": '{{command}}("Hallo")',
            "blanks": [Blank(id="command", options=["print", "input"])],
        },
        {"command": "print"},
    ),
    4: (
        FillBlanksExercise,
        {
            "prompt": "Das Programm soll Hallo und den Namen anzeigen.",
            "code": f'{_GREET}\n{{{{command}}}}("Hallo " + {{{{value}}}})',
            "blanks": [
                Blank(id="command", options=["print", "input"]),
                Blank(id="value", options=["name", '"name"']),
            ],
        },
        {"command": "print", "value": "name"},
    ),
    5: (
        OrderingExercise,
        {
            "prompt": "Bringe die Zeilen in die richtige Reihenfolge.",
            "items": [
                OrderItem(id="show", text="print(gruss)"),
                OrderItem(id="ask", text=_GREET),
                OrderItem(id="build", text='gruss = "Hallo " + name'),
            ],
        },
        {"order": ["ask", "build", "show"]},
    ),
    6: (
        TextBlanksExercise,
        {
            "prompt": "Tippe den Befehl ein, der Text anzeigt.",
            "code": '{{command}}("Hallo")',
            "blanks": [TextBlank(id="command", placeholder="Befehl")],
        },
        {"command": "print"},
    ),
    7: (
        TextBlanksExercise,
        {
            "prompt": "Zeige Hallo und den Namen an. Tippe Befehl und Variable ein.",
            "code": f'{_GREET}\n{{{{command}}}}("Hallo " + {{{{value}}}})',
            "blanks": [
                TextBlank(id="command", placeholder="Befehl"),
                TextBlank(id="value", placeholder="Variable"),
            ],
        },
        {"command": "print", "value": "name"},
    ),
    8: (
        FindBugExercise,
        {
            "prompt": "Python meldet einen Fehler. Welche Zeile ist falsch geschrieben?",
            "lines": [_GREET, 'gruss = "Hallo " + name', "prin(gruss)"],
        },
        {"lines": [3]},
    ),
    9: (
        FindBugExercise,
        {
            "prompt": "Das Programm zeigt immer „Hallo name“. Welche Zeile ist falsch?",
            "lines": [_GREET, 'gruss = "Hallo " + "name"', "print(gruss)"],
        },
        {"lines": [2]},
    ),
    10: (
        FindBugExercise,
        {
            "prompt": "Python kennt gruss noch nicht. Welche Zeile steht zu früh?",
            "lines": [_GREET, "print(gruss)", 'gruss = "Hallo " + name'],
        },
        {"lines": [2]},
    ),
}
_ROUNDS = {"godot": _GODOT, "python": _PYTHON}
_PREFIXES = {"godot": "learn_level", "python": "learn_python"}
_SKILLS = {"godot": "Bewegung und Koordinaten", "python": "Variablen"}


def level_exercise(language: str, level: int) -> Exercise:
    kind, fields, _answers = _ROUNDS[language][level]
    exercise: Exercise = kind(
        id=f"{_PREFIXES[language]}_{level}",
        skill=_SKILLS[language],
        difficulty=min(5, max(1, (level + 1) // 2)),
        **fields,
    )
    return exercise


def level_answers(language: str, level: int) -> dict[str, Any]:
    entry = _ROUNDS[language].get(level)
    return entry[2] if entry else {}


def is_right(language: str, level: int, given: dict[str, Any]) -> bool:
    expected = level_answers(language, level)
    return bool(expected) and all(given.get(key) == value for key, value in expected.items())
