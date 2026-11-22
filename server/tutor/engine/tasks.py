"""Tasks, shared texts and error helper."""

from __future__ import annotations

from typing import Literal

from learnharness_protocol import ErrorMessage, LearningResponse, Task

TASKS: dict[str, Task] = {
    "move_player_right": Task(
        id="move_player_right",
        title="Bewege deinen Spieler nach rechts",
        skill="Koordinaten",
        instructions=(
            "Ändere die Position deines Spielers so, dass er sich nach rechts bewegt. "
            "Schreibe den Code selbst in player.gd."
        ),
        files=["player.gd"],
    ),
    "python_first_program": Task(
        id="python_first_program",
        title="Schreibe dein erstes Python-Programm",
        skill="Variablen",
        instructions=(
            "Lass dein Programm etwas auf dem Bildschirm anzeigen. "
            "Schreibe den Code selbst in main.py."
        ),
        files=["main.py"],
    ),
}


TASK_SKILLS = {"move_player_right": "movement", "python_first_program": "variables"}


TASK_LANGUAGES: dict[str, Literal["gdscript", "python"]] = {"python_first_program": "python"}


UNAVAILABLE = "Der Lernhelfer kann gerade nicht antworten. Versuch es gleich noch einmal."


TOO_FAST = "Langsam – du hast gerade sehr viele Fragen gestellt. Warte kurz und denk selbst nach."


HISTORY_TURNS = 8


Response = LearningResponse | ErrorMessage


def _error(code: str, message: str, retry_after: int | None = None) -> ErrorMessage:
    return ErrorMessage(code=code, message_for_child=message, retry_after=retry_after)
