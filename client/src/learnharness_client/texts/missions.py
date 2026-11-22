"""Code explainer and missions."""

from __future__ import annotations


class MissionTexts:
    # Code explainer
    TAB_EXPLAIN = "Code verstehen"
    EXPLAIN_HEADING = "Code verstehen"
    EXPLAIN_INTRO = (
        "Markiere im Editor ein paar Zeilen und klicke auf „Diesen Code erklären“ – oder "
        "nutze Rechtsklick → „Erklär mir das“. Dann kannst du Fragen dazu stellen."
    )
    EXPLAIN_TAKE_SELECTION = "Diesen Code erklären"
    EXPLAIN_CONTEXT_ACTION = "Erklär mir das"
    EXPLAIN_CODE_A11Y = "Code, der erklärt werden soll"
    EXPLAIN_FILE = "{file}, Zeile {start}–{end}"
    EXPLAIN_NO_CODE = "Öffne zuerst ein Skript und markiere den Code, den du verstehen möchtest."
    EXPLAIN_QUESTIONS = "Fragen zu diesem Code"
    EXPLAIN_OWN_QUESTION = "Eigene Frage stellen …"
    EXPLAIN_OWN_A11Y = "Eigene Frage zum Code"
    EXPLAIN_ASK = "Fragen"
    EXPLAIN_ANSWER = "Erklärung"
    EXPLAIN_THINKING = "Ich schaue mir den Code an …"
    EXPLAIN_CHECK = "Hast du es verstanden? Beantworte diese Frage:"
    EXPLAIN_CORRECT = "Super, du hast es verstanden!"
    EXPLAIN_NOT_YET = "Noch nicht ganz. Lies die Erklärung noch einmal und versuche es erneut."

    # Missions
    TAB_MISSIONS = "Missionen"
    MISSION_HEADING = "Lernmission"
    MISSION_INTRO = (
        "Wähle eine Mission oder beschreibe, was du bauen möchtest. Du arbeitest sie Schritt "
        "für Schritt durch – zum Schluss probierst du alles in Godot aus."
    )
    MISSION_INTRO_PYTHON = (
        "Wähle eine Mission oder beschreibe, was du bauen möchtest. Du arbeitest sie Schritt "
        "für Schritt durch – zum Schluss startest du dein Python-Programm."
    )
    MISSION_SUGGESTIONS = ("Baue einen Doppelsprung!", "Zähle Münzen!")
    MISSION_SUGGESTIONS_PYTHON = ("Baue eine Begrüßung!",)
    MISSION_WISH_PLACEHOLDER_PYTHON = "Oder eigener Wunsch, z. B. „Ein kleiner Taschenrechner“"
    MISSION_WISH_PLACEHOLDER = "Oder eigener Wunsch, z. B. „Meine Figur soll schießen können“"
    MISSION_WISH_A11Y = "Wunsch für eine eigene Mission"
    MISSION_START = "Mission starten"
    MISSION_STARTING = "Ich plane deine Mission …"
    MISSION_PROGRESS = "Missionsfortschritt: {done} von {total}"
    MISSION_STEPS_A11Y = "Schritte der Mission"
    MISSION_DO_STEP = "Schritt starten"
    MISSION_TRY_DONE = "Ich habe es in Godot ausprobiert"
    MISSION_TRY_TEXT = (
        "Speichere dein Skript, starte das Spiel in Godot (F5) und probiere es aus. Klappt "
        "etwas nicht? Frag im Tab „Tutor“ nach."
    )
    MISSION_TRY_DONE_PYTHON = "Ich habe es ausprobiert"
    MISSION_TRY_TEXT_PYTHON = (
        "Speichere dein Skript und starte es im Terminal mit python und dem Dateinamen. Klappt "
        "etwas nicht? Frag im Tab „Tutor“ nach."
    )
    MISSION_STEP_DONE = "Schritt geschafft!"
    MISSION_NOT_YET = "Noch nicht ganz. Versuche es noch einmal."
    MISSION_COMPLETE = "Mission erfüllt: {title} 🎉"
    MISSION_NEW = "Neue Mission"
    MISSION_NEEDS_FILE = "Öffne zuerst das Skript, in dem die Mission gebaut werden soll."
    MISSION_ASSIGNED_HEADING = "Von deiner Lehrkraft"
    MISSION_ASSIGNED_DONE = "✓ {title} (geschafft)"
    MISSION_ASSIGNED_A11Y_DONE = "{title}, schon geschafft"
    MISSION_ASSIGNED_START = "Deine Lehrkraft hat diese Mission ausgesucht: {goal}"
    MISSION_OWN_HEADING = "Eigene Mission"
