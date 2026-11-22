"""Building blocks and code of the demo missions."""

from __future__ import annotations

from dataclasses import dataclass, field

from learnharness_protocol import Blank, Choice, FillBlanksExercise, Mission, MultipleChoiceExercise
from learnharness_protocol.exercises import Exercise


@dataclass(frozen=True, slots=True)
class MissionStepContent:
    message: str
    exercise: Exercise | None = None
    answers: dict[str, str] = field(default_factory=dict)
    code: str | None = None  # released after a correct answer (exercise steps only)


@dataclass(frozen=True, slots=True)
class MissionContent:
    mission: Mission
    keywords: tuple[str, ...]
    steps: dict[str, MissionStepContent]
    language: str = "gdscript"


def _choice(mission_id: str, step: str, prompt: str, right: str, wrong: str) -> Exercise:
    return MultipleChoiceExercise(
        id=f"mission_{mission_id}_{step}",
        skill="Mission",
        difficulty=1,
        prompt=prompt,
        choices=[Choice(id="right", text=right), Choice(id="wrong", text=wrong)],
    )


def _mission_fill(
    mission_id: str, step: str, prompt: str, code: str, options: list[str]
) -> Exercise:
    return FillBlanksExercise(
        id=f"mission_{mission_id}_{step}",
        skill="Mission",
        difficulty=2,
        prompt=prompt,
        code=code,
        blanks=[Blank(id="blank", options=options)],
    )


DOUBLE_JUMP_CODE = (
    "extends CharacterBody2D\n\n"
    "const JUMP_VELOCITY = -400.0\n"
    "# Wie oft die Figur noch springen darf, bevor sie wieder landet.\n"
    "var jumps_left = 2\n\n"
    "func _physics_process(delta: float) -> void:\n"
    "\tif is_on_floor():\n"
    "\t\tjumps_left = 2  # auf dem Boden: wieder zwei Sprünge\n"
    "\telse:\n"
    "\t\tvelocity += get_gravity() * delta\n"
    '\tif Input.is_action_just_pressed("ui_accept") and jumps_left > 0:\n'
    "\t\tvelocity.y = JUMP_VELOCITY\n"
    "\t\tjumps_left -= 1\n"
    "\tmove_and_slide()\n"
)


COIN_CODE = (
    "extends Node2D\n\n"
    "# Hier zählen wir die eingesammelten Münzen.\n"
    "var coins = 0\n\n"
    "func collect_coin() -> void:\n"
    "\tcoins += 1  # eine Münze mehr\n"
    '\tprint("Münzen: ", coins)\n'
)


PYTHON_GREETING_CODE = (
    "# input wartet, bis du etwas eintippst, und merkt es sich in name.\n"
    'name = input("Wie heißt du? ")\n'
    "# print zeigt den Text auf dem Bildschirm an.\n"
    'print(f"Hallo, {name}!")\n'
)


def generic_mission_step(mission_id: str, step_id: str) -> MissionStepContent:
    """For missions a teacher created in the administration: the fake server cannot know
    their content, so it asks one general question (a real learning server uses the notes)."""
    return MissionStepContent(
        message=(
            "Diese Mission hat deine Lehrkraft angelegt. Der Übungsserver kennt ihren Inhalt "
            "nicht genau – der echte Lernserver erklärt dir hier den Schritt."
        ),
        exercise=_choice(
            mission_id,
            step_id,
            "Wie gehst du bei einem neuen Schritt am besten vor?",
            "In kleinen Teilen bauen und nach jedem Teil ausprobieren",
            "Alles auf einmal schreiben und erst am Ende testen",
        ),
        answers={"choice": "right"},
    )
