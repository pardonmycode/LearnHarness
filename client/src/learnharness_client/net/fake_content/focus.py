"""Demo rounds for one skill."""

from __future__ import annotations

from dataclasses import dataclass

from learnharness_protocol import Blank, FillBlanksExercise


@dataclass(frozen=True, slots=True)
class FocusRound:
    label: str
    exercise: FillBlanksExercise
    answers: dict[str, str]
    code: str


def _fill(skill: str, prompt: str, code: str, blanks: dict[str, list[str]]) -> FillBlanksExercise:
    return FillBlanksExercise(
        id=f"learn_focus_{skill}",
        skill=skill,
        difficulty=2,
        prompt=prompt,
        code=code,
        blanks=[Blank(id=blank_id, options=options) for blank_id, options in blanks.items()],
    )


FOCUS_ROUNDS: dict[str, FocusRound] = {
    "conditions": FocusRound(
        "Bedingungen",
        _fill(
            "conditions",
            "Ergänze if und else: Ist die Figur schnell, erscheint „Schnell!“, sonst „Langsam“.",
            '{{first}} speed > 100:\n\tprint("Schnell!")\n{{second}}:\n\tprint("Langsam")',
            {"first": ["if", "for", "var"], "second": ["else", "func", "elif"]},
        ),
        {"first": "if", "second": "else"},
        "extends Node2D\n\n@export var speed: float = 200.0\n\n"
        "func _process(delta: float) -> void:\n"
        "\t# if prüft eine Bedingung, else ist der andere Weg.\n"
        "\tif speed > 100:\n\t\tmodulate = Color.RED\n\telse:\n\t\tmodulate = Color.WHITE\n"
        "\tposition.x += speed * delta\n",
    ),
    "variables": FocusRound(
        "Variablen",
        _fill(
            "variables",
            "Lege eine Variable speed mit dem Wert 200 an.",
            "{{keyword}} speed = 200",
            {"keyword": ["var", "func", "if"]},
        ),
        {"keyword": "var"},
        "extends Node2D\n\n# Eine Variable ist eine Schachtel mit Namen.\nvar speed = 200\n\n"
        "func _process(delta):\n\tposition.x += speed * delta\n",
    ),
    "functions": FocusRound(
        "Funktionen",
        _fill(
            "functions",
            "Mit welchem Wort beginnt eine Funktion?",
            '{{keyword}} _ready():\n\tprint("Los geht\'s")',
            {"keyword": ["func", "var", "if"]},
        ),
        {"keyword": "func"},
        "extends Node2D\n\n# _ready läuft einmal, sobald die Figur im Spiel ist.\n"
        'func _ready():\n\tprint("Los geht\'s")\n',
    ),
}
