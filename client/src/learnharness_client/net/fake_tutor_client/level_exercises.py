"""Exercises and code of the fake LearnAgent levels."""

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


class FakeExercises:
    """Static demo exercises."""

    @staticmethod
    def _fill_blank() -> FillBlanksExercise:
        return FillBlanksExercise(
            id="exercise_001",
            skill="Koordinaten",
            difficulty=1,
            prompt="Welche Eigenschaft bewegt den Spieler nach rechts?",
            code="position.{{blank_1}} += 10",
            blanks=[Blank(id="blank_1", options=["x", "y", "speed"])],
        )

    @staticmethod
    def choice_exercise() -> MultipleChoiceExercise:
        return MultipleChoiceExercise(
            id="exercise_002",
            skill="Koordinaten",
            difficulty=1,
            prompt="Welche Achse ist waagerecht?",
            choices=[
                Choice(id="x_axis", text="X-Achse"),
                Choice(id="y_axis", text="Y-Achse"),
            ],
        )

    @staticmethod
    def _generated_code() -> str:
        return (
            "extends Node2D\n\n"
            "# Geschwindigkeit in Pixeln pro Sekunde.\n"
            "@export var speed: float = 200.0\n\n"
            "func _process(delta: float) -> void:\n"
            "\t# X ist die waagerechte Achse. Ein positiver Wert bewegt nach rechts.\n"
            "\tposition.x += speed * delta\n"
        )

    @staticmethod
    def _exercise_for_level(level: int) -> Exercise:
        common: dict[str, Any] = {
            "id": f"learn_level_{level}",
            "skill": "Bewegung und Koordinaten",
            "difficulty": min(5, max(1, (level + 1) // 2)),
        }
        if level == 1:
            return MultipleChoiceExercise(
                **common,
                prompt="Welche Achse bewegt eine Figur nach links und rechts?",
                choices=[
                    Choice(id="x_axis", text="Die X-Achse"),
                    Choice(id="y_axis", text="Die Y-Achse"),
                ],
            )
        if level == 2:
            return FillBlanksExercise(
                **common,
                prompt="Wähle die waagerechte Achse aus.",
                code="position.{{axis}} += 10",
                blanks=[Blank(id="axis", options=["x", "y"])],
            )
        if level == 3:
            return FillBlanksExercise(
                **common,
                prompt="Ergänze Achse und Geschwindigkeit.",
                code="position.{{axis}} += {{value}} * delta",
                blanks=[
                    Blank(id="axis", options=["x", "y", "z"]),
                    Blank(id="value", options=["position", "speed", "delta"]),
                ],
            )
        if level == 4:
            return TextBlanksExercise(
                **common,
                prompt="Trage Achse und Variable ohne Auswahlhilfe ein.",
                code="position.{{axis}} += {{value}} * delta",
                blanks=[
                    TextBlank(id="axis", placeholder="Achse"),
                    TextBlank(id="value", placeholder="Variable"),
                ],
            )
        if level == 5:
            return OrderingExercise(
                **common,
                prompt="Bringe die Bausteine in die richtige Reihenfolge.",
                items=[
                    OrderItem(id="move", text="position.x += speed * delta"),
                    OrderItem(id="extends", text="extends Node2D"),
                    OrderItem(id="process", text="func _process(delta):"),
                    OrderItem(id="speed", text="var speed = 200.0"),
                ],
            )
        if level == 6:
            return FindBugExercise(
                **common,
                prompt="Welche Zeile bewegt die Figur versehentlich nach unten?",
                lines=[
                    "extends Node2D",
                    "var speed = 200.0",
                    "func _process(delta):",
                    "\tposition.y += speed * delta",
                ],
            )
        if level == 8:
            return TextBlanksExercise(
                **common,
                prompt="Ergänze Funktionsname und Achse.",
                code="func {{function}}(delta):\n\tposition.{{axis}} += speed * delta",
                blanks=[
                    TextBlank(id="function", placeholder="Funktionsname"),
                    TextBlank(id="axis", placeholder="Achse"),
                ],
            )
        if level == 9:
            return MultipleChoiceExercise(
                **common,
                prompt="Wie bleibt die Bewegung unabhängig von der Bildrate?",
                choices=[
                    Choice(id="use_delta", text="Geschwindigkeit mit delta multiplizieren"),
                    Choice(id="fixed_step", text="In jedem Bild immer 10 Pixel addieren"),
                ],
            )
        if level == 10:
            return MultipleChoiceExercise(
                **common,
                prompt="Wie prüfst du den Plan für dein eigenes Feature am besten?",
                choices=[
                    Choice(
                        id="explain_and_test",
                        text="Plan erklären, kleine Schritte testen und Fehler besprechen",
                    ),
                    Choice(id="blind", text="Code ungeprüft übernehmen"),
                ],
            )
        return TextBlanksExercise(
            **common,
            prompt="Ergänze Achse und Geschwindigkeitsvariable.",
            code="position.{{axis}} += {{value}} * delta",
            blanks=[
                TextBlank(id="axis", placeholder="Achse"),
                TextBlank(id="value", placeholder="Variable"),
            ],
        )
