"""Demo explanations of code."""

from __future__ import annotations

from dataclasses import dataclass

from learnharness_protocol import Choice, MultipleChoiceExercise


@dataclass(frozen=True, slots=True)
class Explanation:
    text: str
    question: str
    right: str
    wrong: str


EXPLANATIONS: dict[str, Explanation] = {
    "velocity": Explanation(
        "Mit velocity.x = speed bestimmst du, wie schnell sich deine Spielfigur waagerecht "
        "bewegen soll. Ein positiver Wert bedeutet Bewegung nach rechts, ein negativer nach "
        "links.",
        "Was passiert, wenn speed negativ ist, zum Beispiel -200?",
        "Die Figur bewegt sich nach links.",
        "Die Figur springt nach oben.",
    ),
    "_physics_process": Explanation(
        "_physics_process ist eine Funktion, die Godot von selbst immer wieder aufruft – "
        "ungefähr 60-mal pro Sekunde. Hier steht alles, was sich mit der Bewegung und den "
        "Zusammenstößen deiner Figur beschäftigt.",
        "Wer ruft _physics_process auf?",
        "Godot ruft sie automatisch immer wieder auf.",
        "Ich muss sie selbst einmal aufrufen.",
    ),
    "move_and_slide": Explanation(
        "move_and_slide() bewegt die Figur mit ihrer velocity. Stößt sie an eine Wand oder "
        "den Boden, rutscht sie daran entlang, statt hineinzufallen.",
        "Was nutzt move_and_slide() für die Bewegung?",
        "Die Werte in velocity.",
        "Die Farbe der Figur.",
    ),
    "_process": Explanation(
        "_process wird von Godot in jedem Bild aufgerufen. delta sagt dir, wie viel Zeit "
        "seit dem letzten Bild vergangen ist.",
        "Wie oft ruft Godot _process auf?",
        "In jedem Bild.",
        "Nur einmal beim Start.",
    ),
    "position": Explanation(
        "position ist der Ort deiner Figur. position.x ist links/rechts, position.y ist "
        "oben/unten. In Godot wächst y nach unten.",
        "Was verändert position.y += 10?",
        "Die Figur rutscht ein Stück nach unten.",
        "Die Figur wird größer.",
    ),
    "delta": Explanation(
        "delta ist die Zeit seit dem letzten Bild. Wenn du mit delta multiplizierst, ist "
        "die Bewegung auf schnellen und langsamen Computern gleich schnell.",
        "Warum multipliziert man die Geschwindigkeit mit delta?",
        "Damit sie auf jedem Computer gleich schnell ist.",
        "Damit die Figur unsichtbar wird.",
    ),
    "extends": Explanation(
        "extends sagt, worauf dein Skript aufbaut. Mit extends CharacterBody2D bekommt dein "
        "Skript alles, was eine Spielfigur schon kann, zum Beispiel velocity.",
        "Was bekommt dein Skript durch extends?",
        "Die Fähigkeiten des Knotens, auf dem es aufbaut.",
        "Einen neuen Namen für das Spiel.",
    ),
    "var": Explanation(
        "Mit var legst du eine Variable an – eine Schachtel mit Namen, in der ein Wert "
        "liegt. var speed = 200 legt die Schachtel speed mit dem Wert 200 an.",
        "Was macht var speed = 200?",
        "Es legt eine Variable speed mit dem Wert 200 an.",
        "Es bewegt die Figur sofort um 200 Pixel.",
    ),
    "if": Explanation(
        "Ein if prüft eine Bedingung. Nur wenn sie wahr ist, wird der eingerückte Code "
        "darunter ausgeführt. Mit else sagst du, was sonst passieren soll.",
        "Wann läuft der Code unter if?",
        "Nur wenn die Bedingung wahr ist.",
        "Immer, egal was passiert.",
    ),
}


GENERIC_EXPLANATION = Explanation(
    "Dieser Code sagt Godot Schritt für Schritt, was passieren soll. Lies ihn von oben nach "
    "unten: Jede Zeile ist ein kleiner Auftrag. Eingerückte Zeilen gehören zu der Zeile "
    "darüber.",
    "Was bedeuten eingerückte Zeilen?",
    "Sie gehören zu der Zeile darüber.",
    "Sie werden nie ausgeführt.",
)


PYTHON_EXPLANATION = Explanation(
    "Python liest diesen Code von oben nach unten: Jede Zeile ist ein kleiner Auftrag. "
    "Eingerückte Zeilen gehören zu der Zeile mit dem Doppelpunkt darüber.",
    "Wozu gehören eingerückte Zeilen in Python?",
    "Zu der Zeile mit dem Doppelpunkt darüber.",
    "Zu gar nichts, Python überspringt sie.",
)


def find_explanation(
    question: str, code: str, language: str = "gdscript"
) -> tuple[str, Explanation]:
    """Pick the topic named in the question first, then one that occurs in the code."""
    if language == "python":
        return "python", PYTHON_EXPLANATION
    for text in (question, code):
        for key, explanation in EXPLANATIONS.items():
            if key in text:
                return key, explanation
    return "generic", GENERIC_EXPLANATION


def explanation_question(key: str, explanation: Explanation) -> MultipleChoiceExercise:
    return MultipleChoiceExercise(
        id=f"explain_{key}",
        skill="Code verstehen",
        difficulty=1,
        prompt=explanation.question,
        choices=[
            Choice(id="right", text=explanation.right),
            Choice(id="wrong", text=explanation.wrong),
        ],
    )
