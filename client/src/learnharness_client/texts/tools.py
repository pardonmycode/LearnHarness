"""Godot and Python tools, tutor basics and progress."""

from __future__ import annotations


class ToolTexts:
    # Tutor
    TUTOR_NAME = "Lernhelfer"
    CHILD_NAME = "Du"
    NOTICE_NAME = "Hinweis"
    TUTOR_CONTEXT_DEFAULT = "Dem Lernhelfer wird nur ein kleiner Codeausschnitt gezeigt."
    TUTOR_CONTEXT = "Ich zeige dem Lernhelfer: {file}, Zeilen {start}–{end}."
    TUTOR_OFFLINE_TIP = "Der Lernhelfer macht Pause. Deine Frage bleibt hier stehen."
    AGENT_OFFLINE_TIP = "Der Lernhelfer macht Pause. Du kannst weiter programmieren."

    # Progress
    PROGRESS_OFFLINE = "Stand vom letzten Kontakt mit dem Lernserver."

    # Godot
    GODOT_NOT_SET = (
        "Trage zuerst in den Einstellungen ein, wo Godot liegt (Godot-Programm). "
        "Die Prüfung ist freiwillig – du kannst auch ohne sie weiterarbeiten."
    )
    GODOT_CHECK_RUNNING = "Godot prüft {file} …"
    GODOT_CHECK_OK = "Godot hat in {file} keine Fehler gefunden."
    GODOT_CHECK_ERRORS = (
        "Godot hat {count} Problem(e) gefunden. Sie stehen unten bei den Problemen."
    )
    GODOT_CHECK_FAILED = "Godot konnte nicht prüfen: {reason}"
    GODOT_LOG_MISSING = (
        "Es gibt noch kein Godot-Log. Starte das Spiel einmal in Godot. "
        "Datei-Logging muss in den Projekteinstellungen eingeschaltet sein."
    )
    GODOT_LOG_EMPTY = "Im Godot-Log stehen keine neuen Fehler."
    GODOT_LOG_FOUND = "{count} Fehler aus dem Godot-Log übernommen."

    # Python
    PYTHON_CHECK_OK = "In {file} ist kein Syntaxfehler."
    PYTHON_CHECK_ERROR = "In Zeile {line} stimmt etwas nicht. Schau unten bei den Problemen."
    PYTHON_CHECK_UNREADABLE = "Python kann diese Datei nicht lesen."
    PYTHON_IN_GODOT_PROJECT = (
        "Dieser Ordner ist ein Godot-Projekt. Lege dein Python-Skript in einen eigenen Ordner."
    )

    # Godot process
    GODOT_TIMEOUT = "Godot hat nicht innerhalb von 10 Sekunden geantwortet."
    GODOT_NOT_FOUND = "Das Godot-Programm wurde nicht gefunden."
    GODOT_START_FAILED = "Godot ließ sich nicht starten."
