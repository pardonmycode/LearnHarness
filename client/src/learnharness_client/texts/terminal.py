"""Terminal below the code."""

from __future__ import annotations


class TerminalTexts:
    TERMINAL_HEADING = "TERMINAL"
    TERMINAL_A11Y = "Terminal. Tippe einen Befehl und drücke Enter."
    TERMINAL_WELCOME = "Tippe zum Beispiel {example} und drücke Enter. Mit help siehst du alles."
    TERMINAL_NO_PROJECT = "Öffne zuerst ein Projekt."
    TERMINAL_HELP = (
        "Das kannst du hier tippen:\n"
        "  python main.py   startet ein Python-Skript\n"
        "  godot            startet dein Godot-Spiel\n"
        "  ls               zeigt Ordner und Skripte\n"
        "  cd ordner        wechselt den Ordner (cd .. geht zurück)\n"
        "  pwd              zeigt, wo du gerade bist\n"
        "  clear            leert das Terminal\n"
        "  Strg+C           stoppt ein laufendes Programm"
    )
    TERMINAL_UNKNOWN = "Den Befehl {command} kenne ich nicht. Tippe help für alle Befehle."
    TERMINAL_BAD_QUOTES = "Da fehlt ein Anführungszeichen."
    TERMINAL_PYTHON_NEEDS_FILE = "Sag mir, welche Datei starten soll, zum Beispiel: python main.py"
    TERMINAL_NO_OPTIONS = "Optionen wie {option} gehen hier nicht. Tippe: python datei.py"
    TERMINAL_DID_YOU_MEAN = "Die Datei {file} gibt es nicht. Meinst du: python {suggestion}?"
    TERMINAL_FILE_MISSING = "Die Datei {file} gibt es hier nicht. Mit ls siehst du alle Dateien."
    TERMINAL_NO_FOLDER = "Den Ordner gibt es hier nicht. Mit ls siehst du alle Ordner."
    TERMINAL_PYTHON_IN_GODOT = "Das ist ein Godot-Projekt. Tippe godot, um dein Spiel zu starten."
    TERMINAL_GODOT_IN_PYTHON = "Das ist ein Python-Projekt. Tippe zum Beispiel: python main.py"
    TERMINAL_EMPTY_FOLDER = "(Hier liegen noch keine Skripte.)"
    TERMINAL_STOPPED = "Gestoppt."
    TERMINAL_NOT_STARTED = "Das Programm ließ sich nicht starten."
    TERMINAL_TOO_MUCH = "… (sehr viel Ausgabe, ältere Zeilen wurden ausgelassen) …"
    TERMINAL_NO_PYTHON = (
        "Auf diesem Computer wurde kein Python gefunden. Frag deine Lehrkraft, ob sie es "
        "installieren kann."
    )
