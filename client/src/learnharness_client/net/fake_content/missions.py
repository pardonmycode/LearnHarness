"""The demo missions."""

from __future__ import annotations

from learnharness_protocol import Mission, MissionStep

from .mission_parts import (
    COIN_CODE,
    DOUBLE_JUMP_CODE,
    PYTHON_GREETING_CODE,
    MissionContent,
    MissionStepContent,
    _choice,
    _mission_fill,
)

MISSIONS: dict[str, MissionContent] = {
    "python_greeting": MissionContent(
        Mission(
            id="python_greeting",
            title="Baue eine Begrüßung!",
            goal="Dein Programm fragt nach deinem Namen und begrüßt dich.",
            skill="variables",
            steps=[
                MissionStep(id="understand", title="Verstehen, was input macht", kind="understand"),
                MissionStep(id="greet", title="Die Begrüßung vervollständigen", kind="exercise"),
                MissionStep(id="try", title="Dein Programm starten", kind="try"),
            ],
        ),
        (),
        {
            "understand": MissionStepContent(
                "input zeigt eine Frage an und wartet, bis du etwas eintippst. Deine Antwort "
                "kannst du in einer Variablen speichern.",
                _choice(
                    "python_greeting",
                    "understand",
                    "Was macht input?",
                    "Es wartet auf eine Eingabe.",
                    "Es beendet das Programm.",
                ),
                {"choice": "right"},
            ),
            "greet": MissionStepContent(
                "Jetzt soll dein Programm antworten. Wenn du richtig ergänzt, schreibe ich den "
                "Code mit Erklärungen in dein Skript.",
                _mission_fill(
                    "python_greeting",
                    "greet",
                    "Welcher Befehl zeigt Text auf dem Bildschirm an?",
                    '{{blank}}(f"Hallo, {name}!")',
                    ["print", "input", "len"],
                ),
                {"blank": "print"},
                PYTHON_GREETING_CODE,
            ),
        },
        "python",
    ),
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


def find_mission(wish: str, language: str = "gdscript") -> MissionContent:
    if language == "python":
        return MISSIONS["python_greeting"]
    lowered = wish.casefold()
    for content in MISSIONS.values():
        if any(keyword in lowered for keyword in content.keywords):
            return content
    return MISSIONS["double_jump"]
