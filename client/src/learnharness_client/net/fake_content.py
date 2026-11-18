"""Demo content for the fake server: code explanations, skill-focused rounds, missions.

The real learning server generates this with the language model; the fake only needs
enough content to try out every client feature without a server.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from learnharness_protocol import (
    Blank,
    Choice,
    FillBlanksExercise,
    Mission,
    MissionStep,
    MultipleChoiceExercise,
)
from learnharness_protocol.exercises import Exercise

# --- Code explainer ------------------------------------------------------------------


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


def find_explanation(question: str, code: str) -> tuple[str, Explanation]:
    """Pick the topic named in the question first, then one that occurs in the code."""
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


# --- Skill-focused LearnAgent rounds --------------------------------------------------


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


# --- Missions ---------------------------------------------------------------------------


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

MISSIONS: dict[str, MissionContent] = {
    "double_jump": MissionContent(
        Mission(
            id="double_jump",
            title="Baue einen Doppelsprung!",
            goal="Deine Figur kann in der Luft noch ein zweites Mal springen.",
            skill="conditions",
            steps=[
                MissionStep(
                    id="understand",
                    title="Verstehen, wie der normale Sprung funktioniert",
                    kind="understand",
                ),
                MissionStep(
                    id="variable",
                    title="Eine Variable für die Sprunganzahl kennenlernen",
                    kind="learn",
                ),
                MissionStep(
                    id="condition",
                    title="Eine passende Bedingung vervollständigen",
                    kind="exercise",
                ),
                MissionStep(id="try", title="Den neuen Code in Godot ausprobieren", kind="try"),
            ],
        ),
        ("sprung", "spring", "jump", "hüpf"),
        {
            "understand": MissionStepContent(
                "Beim Springen setzt dein Spiel velocity.y auf einen negativen Wert, zum "
                "Beispiel -400. In Godot zeigt y nach unten – negativ heißt also nach oben. "
                "Danach zieht die Schwerkraft die Figur wieder herunter.",
                _choice(
                    "double_jump",
                    "understand",
                    "Warum ist die Sprunggeschwindigkeit negativ?",
                    "Weil in Godot negative y-Werte nach oben zeigen.",
                    "Weil die Figur sonst zu schnell wird.",
                ),
                {"choice": "right"},
            ),
            "variable": MissionStepContent(
                "Für einen Doppelsprung muss sich das Spiel merken, wie viele Sprünge noch "
                "übrig sind. Dafür brauchst du eine Variable.",
                _mission_fill(
                    "double_jump",
                    "variable",
                    "Lege eine Variable für die übrigen Sprünge an.",
                    "{{blank}} jumps_left = 2",
                    ["var", "func", "if"],
                ),
                {"blank": "var"},
            ),
            "condition": MissionStepContent(
                "Springen darf die Figur nur, wenn die Taste gedrückt wurde UND noch Sprünge "
                "übrig sind. Wenn du das richtig ergänzt, schreibe ich den ganzen Code mit "
                "Erklärungen in dein Skript.",
                _mission_fill(
                    "double_jump",
                    "condition",
                    "Welches Wort verbindet die beiden Bedingungen?",
                    'if Input.is_action_just_pressed("ui_accept") {{blank}} jumps_left > 0:',
                    ["and", "or", "not"],
                ),
                {"blank": "and"},
                DOUBLE_JUMP_CODE,
            ),
        },
    ),
    "coins": MissionContent(
        Mission(
            id="coins",
            title="Zähle Münzen!",
            goal="Dein Spiel zählt, wie viele Münzen die Figur eingesammelt hat.",
            skill="variables",
            steps=[
                MissionStep(
                    id="understand", title="Verstehen, was ein Zähler ist", kind="understand"
                ),
                MissionStep(id="add", title="Eins dazuzählen lernen", kind="learn"),
                MissionStep(
                    id="collect", title="Die Sammel-Funktion vervollständigen", kind="exercise"
                ),
                MissionStep(id="try", title="In Godot ausprobieren", kind="try"),
            ],
        ),
        ("münz", "coin", "sammel", "punkt"),
        {
            "understand": MissionStepContent(
                "Ein Zähler ist eine Variable, die mit 0 anfängt. Jedes Mal, wenn etwas "
                "passiert, wird sie um eins größer.",
                _choice(
                    "coins",
                    "understand",
                    "Womit fängt ein Münzzähler an?",
                    "Mit 0.",
                    "Mit der Anzahl aller Münzen im Level.",
                ),
                {"choice": "right"},
            ),
            "add": MissionStepContent(
                "Mit += zählst du etwas dazu. coins += 1 heißt: nimm coins und lege eins drauf.",
                _mission_fill(
                    "coins", "add", "Zähle eine Münze dazu.", "coins {{blank}} 1", ["+=", "=", "-="]
                ),
                {"blank": "+="},
            ),
            "collect": MissionStepContent(
                "Jetzt kommt alles zusammen. Wenn du richtig antwortest, schreibe ich die "
                "Sammel-Funktion mit Erklärungen in dein Skript.",
                _mission_fill(
                    "coins",
                    "collect",
                    "Mit welchem Wort beginnt die Funktion collect_coin?",
                    "{{blank}} collect_coin() -> void:\n\tcoins += 1",
                    ["func", "var", "if"],
                ),
                {"blank": "func"},
                COIN_CODE,
            ),
        },
    ),
}


def find_mission(wish: str) -> MissionContent:
    lowered = wish.casefold()
    for content in MISSIONS.values():
        if any(keyword in lowered for keyword in content.keywords):
            return content
    return MISSIONS["double_jump"]
