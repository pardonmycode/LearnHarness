"""Window title, menus, tabs, status bar and general messages."""

from __future__ import annotations


class AppTexts:
    APP_TITLE = "LearnHarness – Programmierwerkstatt"
    PROJECT_TITLE = "{project} – LearnHarness"

    # Menus and actions
    MENU_FILE = "&Datei"
    MENU_EDIT = "&Bearbeiten"
    MENU_VIEW = "&Ansicht"
    MENU_CHECK = "&Prüfen"
    MENU_HELP = "&Hilfe"
    OPEN_PROJECT = "Projekt öffnen …"
    NEW_PYTHON_PROJECT = "Neues Python-Projekt …"
    OPEN_PYTHON_SCRIPT = "Python-Skript öffnen …"
    PYTHON_FILE_FILTER = "Python-Skripte (*.py)"
    NEW_SCRIPT = "Neues Skript …"
    SAVE = "Speichern"
    OLDER_VERSIONS = "Ältere Version ansehen …"
    RECENT_PROJECTS = "Zuletzt verwendete Projekte"
    QUIT = "Beenden"
    FIND = "Suchen"
    REPLACE = "Suchen und ersetzen"
    GOTO_LINE = "Gehe zu Zeile …"
    SETTINGS = "Einstellungen …"
    SHOW_PROBLEMS = "Probleme anzeigen"
    SYNTAX_CHECK = "Skript mit Godot prüfen"
    SYNTAX_CHECK_PYTHON = "Python-Skript prüfen"
    READ_GODOT_LOG = "Fehler aus dem Godot-Log holen"
    TUTORIAL = "Kurzanleitung"
    DIAGNOSTICS = "Technische Details"

    # Tabs and docks
    TAB_AGENT = "LearnAgent"
    TAB_PROJECT = "Projekt"
    TAB_TUTOR = "Tutor"
    TAB_PROGRESS = "Fortschritt"
    PROBLEMS_DOCK = "Probleme und Fehlermeldungen"

    # Status bar
    NO_PROJECT = "Kein Projekt geöffnet"
    NO_FILE = "Keine Datei"
    PROFILE = "Profil: {pseudonym} · {experience}"
    CURSOR = "Zeile {line} · Spalte {column}"
    CURSOR_EMPTY = "Zeile – · Spalte –"
    CONNECTION_CHECKING = "● Lernhelfer wird geprüft"
    CONNECTION_ONLINE = "● Der Lernhelfer ist da"
    CONNECTION_OFFLINE = "● Der Lernhelfer macht Pause"
    CONNECTION_ONLINE_TIP = "Du kannst Fragen stellen."
    CONNECTION_OFFLINE_TIP = "Du kannst trotzdem weiter programmieren und speichern."
    PROJECT_OPENED = "Projekt geöffnet. Du kannst auch ohne Lernserver arbeiten."

    # Messages
    OPEN_PROJECT_FIRST_TITLE = "Erst Projekt öffnen"
    OPEN_PROJECT_FIRST = "Öffne zuerst ein Projekt."
    OPEN_FILE_FIRST = "Öffne zuerst eine Skriptdatei."
    NEW_SCRIPT_PROMPT = "Dateiname, zum Beispiel enemy.gd:"
    NEW_SCRIPT_PROMPT_PYTHON = "Dateiname, zum Beispiel rechner.py:"
    NEW_PYTHON_PROJECT_PROMPT = "Wie soll dein Projekt heißen?"
    NEW_PYTHON_PROJECT_WHERE = "Wo soll der Projektordner liegen?"
    PROJECT_NOT_CREATED = "Projekt nicht angelegt"
    GOTO_LINE_PROMPT = "Zeilennummer:"
    WAIT_FOR_SESSION = "Öffne zuerst ein Projekt und warte kurz auf den Lernserver."
    AGENT_NEEDS_FILE = "Öffne zuerst die Skriptdatei, die der LearnAgent später schreiben soll."
    PROJECT_NOT_OPENED = "Projekt nicht geöffnet"
    SETTINGS_SAVED_TITLE = "Einstellungen gespeichert"
    SETTINGS_SAVED = (
        "Automatisches Speichern und die Änderungsansicht gelten sofort. "
        "Netzwerk- und Anzeigeeinstellungen gelten beim nächsten Start."
    )
    NO_BACKUPS = "Für {file} gibt es noch keine älteren Versionen."
    VERSION_RESTORED = "Ältere Version von {file} in den Editor geholt. Speichern mit Strg+S."

    # App start
    CRASH_TITLE = "Etwas ist schiefgegangen"
    CRASH = "Dein ungespeicherter Text wurde als Entwurf gesichert. Bitte starte LearnHarness neu."
    CHOOSE_PROJECT = "Projektordner auswählen"
    NOT_A_PROJECT_TITLE = "Kein Projekt gefunden"
