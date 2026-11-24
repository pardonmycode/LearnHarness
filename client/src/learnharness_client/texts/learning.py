"""Tutor panel, LearnAgent, progress and exercises."""

from __future__ import annotations


class LearningTexts:
    # Tutor panel controls
    TUTOR_HISTORY_A11Y = "Gespräch mit dem Lernhelfer"
    TUTOR_INPUT_PLACEHOLDER = "Schreibe deine Frage … (Strg+Enter sendet)"
    TUTOR_INPUT_A11Y = "Frage an den Lernhelfer"
    TUTOR_HINT_PROGRESS = "Hinweisstufe %v von %m"
    TUTOR_SEND = "Frage senden"
    TUTOR_NEXT_HINT = "Nächster Hinweis"
    TUTOR_HINT_REQUEST = "Ich brauche Hinweis {level} von 4."
    TUTOR_STOP = "Stopp"
    TUTOR_REVIEW = "Code prüfen lassen"
    TUTOR_REVIEW_TIP = "Der Lernhelfer schaut sich dein geöffnetes Skript an und gibt dir Tipps."
    TUTOR_REVIEW_REQUEST = "Bitte prüfe meinen Code in {file}."
    TUTOR_REVIEW_NEEDS_FILE = "Öffne zuerst das Skript, das ich prüfen soll."

    # LearnAgent panel
    AGENT_HEADING = "LearnAgent"
    AGENT_INTRO = (
        "Beschreibe, was dein Projekt können soll. Der Agent erklärt zuerst das Thema und "
        "stellt dir eine Lernfrage. Erst wenn deine Antwort richtig ist, schreibt er den "
        "Code in dein Projekt."
    )
    AGENT_LEVEL_SECTION = "DEIN LEVEL"
    AGENT_LEVEL_A11Y = "LearnAgent-Level"
    AGENT_LEVEL = "Level {level}"
    AGENT_LEVEL_LOCKED = "Level {level}  🔒"
    AGENT_UNLOCKED = "{level} von 10 freigeschaltet"
    AGENT_UNLOCKED_A11Y = "Freigeschaltete Level"
    AGENT_WISH_SECTION = "WAS SOLL DEIN PROJEKT KÖNNEN?"
    AGENT_WISH_PLACEHOLDER = "Zum Beispiel: Meine Figur soll nach rechts laufen."
    AGENT_WISH_PLACEHOLDER_PYTHON = "Zum Beispiel: Mein Programm soll mich begrüßen."
    AGENT_WISH_A11Y = "Wunsch an den LearnAgent"
    AGENT_START = "Lernrunde starten  →"
    AGENT_WISH_EMPTY = "Beschreibe zuerst kurz deinen Wunsch."
    AGENT_PREPARING = "Der LearnAgent bereitet eine passende Lernfrage vor …"
    AGENT_CORRECT = "✓  Richtig! Jetzt darf der LearnAgent den vollständigen Code schreiben."
    AGENT_NOT_YET = (
        "Noch nicht ganz – dein Projekt wurde nicht verändert. "
        "Lies den Hinweis unten und versuche es noch einmal."
    )
    AGENT_CODE_WRITTEN = (
        "✓  Geschafft! Der LearnAgent hat den Code in {files} geschrieben. "
        "Vorher wurde eine Sicherung angelegt – mit Strg+Z im Editor siehst du deinen "
        "alten Code wieder.\n\nSo funktioniert der Code:\n{explanation}"
    )
    AGENT_CODE_FAILED = (
        "Die Antwort war richtig, aber der Code konnte nicht geschrieben werden. "
        "Dein bisheriger Inhalt wurde nicht überschrieben."
    )
    LEVEL_DESCRIPTIONS = {
        1: "Einfache Verständnisfragen. Erst nach einer richtigen Antwort schreibt der Agent "
        "den Code.",
        2: "Auswahlfragen zu deinem Code mit kurzen Erklärungen.",
        3: "Eine Code-Lücke mit einem Dropdown-Menü.",
        4: "Schwierigere Code-Lücken mit einem oder zwei Dropdown-Menüs.",
        5: "Bringe fertige Code-Zeilen in die richtige Reihenfolge.",
        6: "Tippe einen kurzen Ausdruck selbst ein.",
        7: "Tippe ein oder zwei kurze Ausdrücke selbst ein.",
        8: "Finde die falsche Zeile in einem kurzen Code-Beispiel.",
        9: "Finde einen Fehler im Ablauf oder in der Logik.",
        10: "Finde einen kniffligen Fehler fast ohne Hinweise.",
    }

    # Progress panel
    PROGRESS_HEADING = "Deine Fähigkeiten"
    PROGRESS_INTRO = (
        "Hier siehst du, was du schon kannst. Es gibt keine Punkte und keine Rangliste."
    )
    LEVEL_WORDS = {
        0: "noch nicht begonnen",
        1: "mit Hilfe",
        2: "fast allein",
        3: "sicher",
    }

    # Exercises
    EXERCISE_TAG = "Übung · {skill}"
    EXERCISE_SUBMIT = "Antwort prüfen"
    EXERCISE_CHECKING = "Wird geprüft …"
    EXERCISE_DONE = "✓ Geschafft"
    EXERCISE_RETRY = "Nochmal prüfen"
    EXERCISE_FOLLOW_UP = "\n\nWeiterdenken: {question}"
    EXERCISE_UNKNOWN = "Diese Übungsart kann ich noch nicht anzeigen."
    EXERCISE_MORE_BLANKS = "# weitere Lücken:"
    BLANK = "Lücke {index}"
    BLANK_CHOOSE = "{index}: wählen …"
    BLANKS_CODE_A11Y = "Code mit Lücken: {code}"
    TEXT_BLANKS_CODE_A11Y = "Code mit freien Textlücken: {code}"
    FIND_BUG_LINES_A11Y = "Codezeilen – wähle die fehlerhafte Zeile"
    FIND_BUG_EXPLANATION = "Optional: Warum ist diese Zeile auffällig?"
    CHOICE_CODE_A11Y = "Code zur Frage"
    ORDERING_A11Y = "Elemente in die richtige Reihenfolge bringen"

    # Skill focus in the LearnAgent
    FOCUS_SECTION = "Was möchtest du üben?"
    FOCUS_AUTO = "Automatisch: {label}"
    FOCUS_AUTO_NONE = "Automatisch"
    FOCUS_SKILL = "{label} · {level}"
    FOCUS_A11Y = "Übungsschwerpunkt"
    FOCUS_HINT = (
        "„Automatisch“ wählt die Fähigkeit, bei der du noch am meisten Übung brauchst. Der "
        "LearnAgent stellt dir Aufgaben dazu, statt einfach immer schwerer zu werden. Code "
        "schreibt er trotzdem erst nach einer richtigen Antwort."
    )
