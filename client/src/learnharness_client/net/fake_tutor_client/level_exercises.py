"""Exercises and code of the fake LearnAgent levels."""

from __future__ import annotations

from learnharness_protocol import (
    Blank,
    Choice,
    FillBlanksExercise,
    MultipleChoiceExercise,
)
from learnharness_protocol.exercises import Exercise

from .level_content import level_exercise


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
        return level_exercise("godot", level)
