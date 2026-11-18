"""Central child-facing UI texts (German, simple sentences).

All texts of the main window, panels and dialogs live here so a later ``QTranslator``
or a second language only needs one place. Placeholders use ``str.format`` names.
"""

from __future__ import annotations


class T:
    APP_TITLE = "LearnHarness – Godot-Programmierwerkstatt"
    PROJECT_TITLE = "{project} – LearnHarness"

    # Menus and actions
    MENU_FILE = "&Datei"
    MENU_EDIT = "&Bearbeiten"
    MENU_VIEW = "&Ansicht"
    MENU_GODOT = "&Godot"
    MENU_HELP = "&Hilfe"
    OPEN_PROJECT = "Godot-Projekt öffnen …"
    NEW_SCRIPT = "Neues GDScript …"
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
    READ_GODOT_LOG = "Fehler aus dem Godot-Log holen"
    TUTORIAL = "Kurzanleitung"
    DIAGNOSTICS = "Technische Details"

    # Tabs and docks
    TAB_AGENT = "LearnAgent"
    TAB_TUTOR = "Tutor"
    TAB_PROGRESS = "Fortschritt"
    PROBLEMS_DOCK = "Probleme und Godot-Fehler"

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
    OPEN_PROJECT_FIRST = "Öffne zuerst ein Godot-Projekt."
    OPEN_FILE_FIRST = "Öffne zuerst eine GDScript-Datei."
    NEW_SCRIPT_PROMPT = "Dateiname, zum Beispiel enemy.gd:"
    GOTO_LINE_PROMPT = "Zeilennummer:"
    WAIT_FOR_SESSION = "Öffne zuerst ein Projekt und warte kurz auf den Lernserver."
    AGENT_NEEDS_FILE = "Öffne zuerst die GDScript-Datei, die der LearnAgent später schreiben soll."
    PROJECT_NOT_OPENED = "Projekt nicht geöffnet"
    SETTINGS_SAVED_TITLE = "Einstellungen gespeichert"
    SETTINGS_SAVED = "Die neuen Netzwerk- und Anzeigeeinstellungen gelten beim nächsten Start."
    NO_BACKUPS = "Für {file} gibt es noch keine älteren Versionen."
    VERSION_RESTORED = "Ältere Version von {file} in den Editor geholt. Speichern mit Strg+S."

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

    # First start
    FIRST_START_TITLE = "Willkommen! Wo ist der Lernserver?"
    FIRST_START_INTRO = (
        "LearnHarness braucht die Adresse des Lernservers. Du bekommst sie von der Person, "
        "die den Server eingerichtet hat. Du kannst das auch später in den Einstellungen ändern."
    )
    FIRST_START_ADDRESS = "Adresse:"
    FIRST_START_TEST = "Verbindung testen"
    FIRST_START_TESTING = "Ich prüfe die Verbindung …"
    FIRST_START_OK = "✓ Der Lernserver antwortet."
    FIRST_START_SERVER_ONLY = (
        "Der Lernserver antwortet, aber das Sprachmodell ist noch nicht bereit."
    )
    FIRST_START_FAILED = (
        "Der Lernserver antwortet nicht. Prüfe die Adresse und ob Tailscale verbunden ist."
    )
    FIRST_START_FAKE = "Erst einmal ohne Lernserver üben (eingebauter Übungsserver)"
    FIRST_START_DONE = "Fertig"

    # Tutorial
    TUTORIAL_TITLE = "So funktioniert die Werkstatt"
    TUTORIAL_SKIP = "Überspringen"
    TUTORIAL_NEXT = "Weiter"
    TUTORIAL_BACK = "Zurück"
    TUTORIAL_FINISH = "Los geht's!"
    TUTORIAL_STEP = "Schritt {current} von {total}"
    TUTORIAL_STEPS = (
        (
            "1. Dein Godot-Projekt",
            "Links siehst du die Skripte deines Spiels. Mit einem Doppelklick öffnest du eins. "
            "Mit Strg+S speicherst du – Godot sieht die Änderung sofort.",
        ),
        (
            "2. Der LearnAgent",
            "Rechts beschreibst du, was dein Spiel können soll. Der Agent stellt dir zuerst "
            "eine Lernfrage. Erst wenn deine Antwort stimmt, schreibt er den Code.",
        ),
        (
            "3. Der Lernhelfer",
            "Im Tab „Tutor“ kannst du Fragen stellen. Der Lernhelfer gibt dir Hinweise, "
            "aber keine fertigen Lösungen. „Nächster Hinweis“ hilft dir Schritt für Schritt.",
        ),
        (
            "4. Keine Angst vor Fehlern",
            "Vor jedem Speichern wird eine Sicherung angelegt. Über „Datei → Ältere Version "
            "ansehen“ findest du deinen alten Code wieder.",
        ),
    )

    # Older versions
    BACKUP_TITLE = "Ältere Versionen von {file}"
    BACKUP_INTRO = (
        "Vor jedem Speichern wurde eine Sicherung angelegt. Wähle links eine Version aus. "
        "Du kannst daraus kopieren oder die ganze Version zurückholen."
    )
    BACKUP_RESTORE = "Diese Version wiederherstellen"
    BACKUP_CLOSE = "Schließen"
    BACKUP_CONFIRM_TITLE = "Version wiederherstellen?"
    BACKUP_CONFIRM = (
        "Der Editor zeigt dann diese ältere Version. Deine jetzige Version ist nicht verloren: "
        "Mit Strg+Z holst du sie zurück, und beim Speichern entsteht wieder eine Sicherung."
    )
