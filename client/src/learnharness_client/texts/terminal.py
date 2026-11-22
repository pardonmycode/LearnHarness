"""Terminal below the code."""

from __future__ import annotations


class TerminalTexts:
    MENU_RUN = "&Starten"
    RUN_START = "Starten"
    RUN_STOP = "Stoppen"
    TERMINAL_HEADING = "TERMINAL"
    TERMINAL_START_SCRIPT = "▶  {file} starten"
    TERMINAL_START_GAME = "▶  Spiel starten"
    TERMINAL_START_EMPTY = "▶  Starten"
    TERMINAL_STOP = "■  Stopp"
    TERMINAL_CLEAR = "Leeren"
    TERMINAL_OUTPUT_A11Y = "Ausgabe deines Programms"
    TERMINAL_INPUT_A11Y = "Eingabe für dein Programm"
    TERMINAL_INPUT_PLACEHOLDER = "Eingabe für dein Programm, Enter schickt sie ab …"
    TERMINAL_IDLE = "Drücke Starten (F5), um dein Programm auszuführen."
    TERMINAL_STARTED = "▶ {file} läuft …"
    TERMINAL_FINISHED = "✓ Fertig."
    TERMINAL_FAILED = "✗ Dein Programm wurde mit einem Fehler beendet (Code {code})."
    TERMINAL_STOPPED = "■ Gestoppt."
    TERMINAL_NOT_STARTED = "Das Programm ließ sich nicht starten."
    TERMINAL_TOO_MUCH = "… (sehr viel Ausgabe, ältere Zeilen wurden ausgelassen) …"
    TERMINAL_NO_SCRIPT = "Öffne zuerst ein Python-Skript."
    TERMINAL_NO_PYTHON = (
        "Auf diesem Computer wurde kein Python gefunden. Frag deine Lehrkraft, ob sie es "
        "installieren kann."
    )
