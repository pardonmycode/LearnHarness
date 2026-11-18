"""Central child-facing UI texts (German, simple sentences).

Every text a child can see lives here – windows, panels, dialogs, exercises and the
error messages raised by the domain and network layers – so a later ``QTranslator`` or a
second language only needs this one module. Placeholders use ``str.format`` names.
Exercise content itself comes from the learning server and is not translated here.
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
    SETTINGS_SAVED = (
        "Automatisches Speichern und die Änderungsansicht gelten sofort. "
        "Netzwerk- und Anzeigeeinstellungen gelten beim nächsten Start."
    )
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

    # App start
    CRASH_TITLE = "Etwas ist schiefgegangen"
    CRASH = "Dein ungespeicherter Text wurde als Entwurf gesichert. Bitte starte LearnHarness neu."
    CHOOSE_PROJECT = "Godot-Projekt auswählen"
    NOT_A_PROJECT_TITLE = "Kein Godot-Projekt"

    # Domain errors (shown to the child via QMessageBox)
    PATH_NOT_PROJECT = "Der gewählte Ordner ist kein Godot-Projekt."
    PATH_LINKED = "Verknüpfte Ordner und Dateien sind hier nicht erlaubt."
    PATH_PROTECTED = "Dieser Projektordner ist geschützt."
    PATH_ADDONS = "Add-ons sind standardmäßig ausgeblendet."
    PATH_GDIGNORE = "Dieser Ordner wird von Godot ignoriert."
    PATH_OUTSIDE = "Die Datei liegt außerhalb des Godot-Projekts."
    PATH_NOT_FOUND = "Die Skriptdatei wurde nicht gefunden."
    PATH_ONLY_GD = "Es dürfen nur GDScript-Dateien geöffnet werden."
    PATH_NOT_FILE = "Der Pfad ist keine Skriptdatei."
    PROJECT_MISSING_DESCRIPTOR = "In diesem Ordner fehlt die Datei project.godot."
    FILE_TOO_LARGE = "Diese Datei ist zu groß für den Lerneditor."
    FILE_NOT_UTF8 = "Die Datei ist nicht als UTF-8 gespeichert."
    FILE_CHANGED_ON_DISK = (
        "Die Datei wurde seit dem Öffnen in Godot oder einem anderen Programm geändert."
    )
    FILE_OPEN_FAILED = "Die Datei konnte nicht zum Speichern geöffnet werden."
    FILE_WRITE_INCOMPLETE = "Die Datei konnte nicht vollständig geschrieben werden."
    FILE_COMMIT_FAILED = "Das sichere Speichern konnte nicht abgeschlossen werden."
    FILE_EXISTS = "Diese Datei gibt es bereits."
    PSEUDONYM_LENGTH = "Der Spitzname muss zwischen 2 und 30 Zeichen lang sein."
    PSEUDONYM_CHARACTERS = "Der Spitzname enthält ungültige Zeichen."
    PROFILE_ID_MISSING = "Die Profil-ID fehlt."
    EXPERIENCE_FIRST_STEPS = "Erste Schritte"
    EXPERIENCE_BASICS = "Ich kenne die Grundlagen"
    EXPERIENCE_SOME_PROJECTS = "Ich habe schon kleine Projekte gebaut"
    EXPERIENCE_INDEPENDENT = "Ich programmiere oft selbstständig"

    # Login
    LOGIN_TITLE = "Wer programmiert heute?"
    LOGIN_HEADING = "Willkommen in der Godot-Programmierwerkstatt!"
    LOGIN_INTRO = (
        "Wähle dein Profil oder lege ein neues an. Benutze bitte einen Spitznamen, "
        "nicht deinen vollständigen Namen. Die Erfahrungsstufe hilft dem Lernhelfer, "
        "passende Fragen und Hinweise zu geben."
    )
    LOGIN_PROFILE_A11Y = "Gespeichertes Lernprofil"
    LOGIN_NEW_PROFILE = "Neues Profil anlegen …"
    LOGIN_PSEUDONYM_PLACEHOLDER = "Zum Beispiel: CodeFuchs"
    LOGIN_PSEUDONYM_A11Y = "Spitzname"
    LOGIN_EXPERIENCE_A11Y = "Erfahrung beim Programmieren"
    LOGIN_PROFILE = "Profil:"
    LOGIN_PSEUDONYM = "Spitzname:"
    LOGIN_EXPERIENCE = "Meine Erfahrung:"
    LOGIN_PRIVACY = (
        "Dieses Profil wird nur auf diesem Computer gespeichert. Es ist kein Passwort nötig."
    )
    LOGIN_BUTTON = "Anmelden"
    LOGIN_INCOMPLETE = "Profil noch nicht vollständig"

    # Settings
    SETTINGS_TITLE = "Einstellungen"
    SETTINGS_FAKE_SERVER = "Eingebauten Übungsserver verwenden"
    SETTINGS_GODOT_PLACEHOLDER = "Optional, z. B. C:\\Godot\\Godot_v4.exe"
    SETTINGS_GODOT_A11Y = "Pfad zum Godot-Programm"
    SETTINGS_BROWSE = "Suchen …"
    SETTINGS_SERVER = "Lernserver-Adresse:"
    SETTINGS_SERVER_A11Y = "Lernserver-Adresse"
    SETTINGS_GODOT = "Godot-Programm:"
    SETTINGS_DEVELOPMENT = "Entwicklung:"
    SETTINGS_FONT_SIZE = "Schriftgröße:"
    SETTINGS_FONT_SIZE_A11Y = "Schriftgröße"
    SETTINGS_THEME = "Darstellung:"
    SETTINGS_THEME_A11Y = "Darstellung"
    SETTINGS_CHOOSE_GODOT = "Godot-Programm auswählen"
    SETTINGS_GODOT_FILTER = "Programme (*.exe);;Alle (*)"
    THEME_SYSTEM = "Wie Windows"
    THEME_LIGHT = "Hell"
    THEME_DARK = "Dunkel"
    THEME_HIGH_CONTRAST = "Hoher Kontrast"
    FIRST_START_ADDRESS_A11Y = "Adresse des Lernservers"

    # Conflict and recovery dialogs
    CONFLICT_TITLE = "Die Datei wurde auch in Godot geändert"
    CONFLICT_INTRO = (
        "Deine Version und die Version auf der Festplatte sind verschieden. "
        "Wähle bewusst, welche Version du behalten möchtest."
    )
    CONFLICT_DISK_VERSION = "Version aus Godot"
    CONFLICT_MY_VERSION = "Meine Version"
    CONFLICT_SAME = "Die Texte sehen gleich aus."
    CONFLICT_KEEP_MINE = "Meine Version behalten"
    CONFLICT_LOAD_DISK = "Version aus Godot laden"
    CONFLICT_CANCEL = "Erst einmal nichts ändern"
    CONFLICT_DELETED = "(Die Datei wurde gelöscht.)"
    RECOVERY_TITLE = "Ungespeicherte Arbeit gefunden"
    RECOVERY_INTRO = "Für {file} gibt es einen Entwurf von vor dem letzten Beenden."
    RECOVERY_RESTORE = "Im Editor wiederherstellen"
    RECOVERY_DISCARD = "Entwurf verwerfen"
    RECOVERY_LATER = "Später entscheiden"

    # Editor
    FIND_PLACEHOLDER = "Suchen"
    FIND_LABEL = "Suchen:"
    REPLACE_PLACEHOLDER = "Ersetzen"
    FIND_NEXT = "Weiter"
    REPLACE_BUTTON = "Ersetzen"
    CLOSE = "Schließen"
    FILE_NOT_OPENED = "Datei nicht geöffnet"
    FILE_NOT_CREATED = "Datei nicht angelegt"
    AGENT_CODE_NOT_WRITTEN = "Agenten-Code nicht geschrieben"
    AGENT_CREATED_FILE = "LearnAgent hat {file} angelegt."
    AGENT_WROTE_FILE = "LearnAgent hat {file} vollständig geschrieben."
    UNSAVED_OWN_CODE_TITLE = "Ungespeicherter eigener Code"
    UNSAVED_OWN_CODE = (
        "Der LearnAgent überschreibt keine ungespeicherten Änderungen. "
        "Speichere oder verwerfe sie und versuche es danach erneut."
    )
    SAVED = "Gespeichert: {file}"
    SAVE_FAILED_TITLE = "Speichern nicht möglich"
    SAVE_FAILED = "Dein Text bleibt im Editor und wurde als Entwurf gesichert.\n\n{error}"
    RELOADED_FROM_GODOT = "Neu aus Godot geladen: {file}"
    DELETED_EXTERNALLY = "{file} wurde außerhalb des Editors gelöscht. Dein Text bleibt geöffnet."
    KEEPING_MY_VERSION = "Deine Version bleibt im Editor. Speichere sie bewusst mit Strg+S."
    UNSAVED_CHANGES_TITLE = "Ungespeicherte Änderungen"
    UNSAVED_CHANGES = "Möchtest du {file} vor dem Schließen speichern?"

    # Script tree
    SCRIPTS = "Skripte"
    SCRIPTS_A11Y = "Skriptdateien im Godot-Projekt"

    # Problems
    PROBLEM_INPUT_PLACEHOLDER = "Godot-Fehlermeldung hier einfügen …"
    PROBLEM_INPUT_A11Y = "Godot-Fehlermeldung einfügen"
    PROBLEM_ADD = "Fehler hinzufügen"
    PROBLEM_LIST_A11Y = "Liste der Probleme"
    SOURCE_GODOT = "Godot"
    SOURCE_GODOT_CHECK = "Godot-Prüfung"
    SOURCE_GODOT_LOG = "Godot-Log"
    SOURCE_REVIEW = "Prüfung"

    # Diagnostics
    DIAG_NOT_CHECKED = "Noch nicht geprüft"
    DIAG_NO_SESSION = "keine Sitzung"
    DIAG_SESSION_ACTIVE = "aktiv ({session})"
    DIAG_SERVER = "Lernserver:"
    DIAG_PROTOCOL = "Protokoll:"
    DIAG_SERVER_STATE = "Server:"
    DIAG_MODEL = "Modell:"
    DIAG_SESSION = "Sitzung:"
    DIAG_LATENCY = "Latenz:"
    DIAG_LAST_ERROR = "Letzter Fehler:"
    DIAG_REACHABLE = "erreichbar"
    DIAG_UNREACHABLE = "nicht erreichbar"
    DIAG_READY = "bereit"
    DIAG_NOT_READY = "nicht bereit"
    DIAG_LATENCY_MS = "{ms} ms"

    # Tutor panel controls
    TUTOR_HISTORY_A11Y = "Gespräch mit dem Lernhelfer"
    TUTOR_INPUT_PLACEHOLDER = "Schreibe deine Frage … (Strg+Enter sendet)"
    TUTOR_INPUT_A11Y = "Frage an den Lernhelfer"
    TUTOR_HINT_PROGRESS = "Hinweisstufe %v von %m"
    TUTOR_SEND = "Frage senden"
    TUTOR_NEXT_HINT = "Nächster Hinweis"
    TUTOR_STOP = "Stopp"

    # LearnAgent panel
    AGENT_HEADING = "LearnAgent"
    AGENT_INTRO = (
        "Beschreibe, was dein Spiel können soll. Der Agent erklärt zuerst das Thema und "
        "stellt dir eine Lernfrage. Erst wenn deine Antwort richtig ist, schreibt er den "
        "Code in dein Projekt."
    )
    AGENT_LEVEL_SECTION = "DEIN LEVEL"
    AGENT_LEVEL_A11Y = "LearnAgent-Level"
    AGENT_LEVEL = "Level {level}"
    AGENT_LEVEL_LOCKED = "Level {level}  🔒"
    AGENT_UNLOCKED = "{level} von 10 freigeschaltet"
    AGENT_UNLOCKED_A11Y = "Freigeschaltete Level"
    AGENT_WISH_SECTION = "WAS SOLL DEIN SPIEL KÖNNEN?"
    AGENT_WISH_PLACEHOLDER = "Zum Beispiel: Meine Figur soll nach rechts laufen."
    AGENT_WISH_A11Y = "Wunsch an den LearnAgent"
    AGENT_START = "Lernrunde starten  →"
    AGENT_WISH_EMPTY = "Beschreibe zuerst kurz deinen Spielwunsch."
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
        2: "Einfache Code-Lücken mit einem Dropdown-Menü.",
        3: "Schwierigere Code-Lücken mit mehreren Dropdown-Menüs.",
        4: "Code-Lücken ohne Auswahl: Du trägst kurze Begriffe selbst ein.",
        5: "Bringe fertige Code-Bausteine in die richtige Reihenfolge.",
        6: "Finde einen Fehler in einem kurzen Code-Beispiel.",
        7: "Ergänze wichtige Ausdrücke mit kleinen Hinweisen.",
        8: "Plane eine Funktion und ergänze mehrere zusammenhängende Teile.",
        9: "Entscheide selbst über den Lösungsweg und begründe ihn.",
        10: "Beschreibe ein eigenes Spielfeature und prüfe den Plan des Agenten.",
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

    # Backup dialog details
    BACKUP_LIST_A11Y = "Liste der älteren Versionen"
    BACKUP_PREVIEW_A11Y = "Inhalt der ausgewählten älteren Version"
    BACKUP_UNREADABLE = "(Diese Sicherung kann nicht gelesen werden: {error})"
    BACKUP_TODAY = "Heute, {time} Uhr"
    BACKUP_DATE = "{date} Uhr"

    # Godot process
    GODOT_TIMEOUT = "Godot hat nicht innerhalb von 10 Sekunden geantwortet."
    GODOT_NOT_FOUND = "Das Godot-Programm wurde nicht gefunden."
    GODOT_START_FAILED = "Godot ließ sich nicht starten."

    # Project choice
    PROJECT_CHOICE_TITLE = "Welches Spiel möchtest du bearbeiten?"
    PROJECT_CHOICE_INTRO = (
        "Diese Godot-Projekte habe ich auf deinem Computer gefunden. Wähle eins aus."
    )
    PROJECT_CHOICE_LIST_A11Y = "Gefundene Godot-Projekte"
    PROJECT_CHOICE_RECENT_TAG = "Zuletzt benutzt · {path}"
    PROJECT_CHOICE_GODOT_TAG = "Aus Godot · {path}"
    PROJECT_CHOICE_OPEN = "Öffnen"
    PROJECT_CHOICE_OTHER_FOLDER = "Anderen Ordner wählen …"
    PROJECT_CHOICE_CANCEL = "Abbrechen"

    # Teacher area
    TEACHER_MENU = "Lehrkraft-Bereich …"
    TEACHER_TITLE = "Lehrkraft-Bereich"
    TEACHER_SET_PASSWORD_INTRO = (
        "Lege einmalig ein Passwort für den Lehrkraft-Bereich fest. Kinder brauchen es nicht."
    )
    TEACHER_PASSWORD = "Passwort:"
    TEACHER_PASSWORD_REPEAT = "Wiederholen:"
    TEACHER_PASSWORD_A11Y = "Passwort für den Lehrkraft-Bereich"
    TEACHER_PASSWORD_TOO_SHORT = "Das Passwort braucht mindestens 6 Zeichen."
    TEACHER_PASSWORD_MISMATCH = "Die beiden Passwörter stimmen nicht überein."
    TEACHER_PASSWORD_WRONG = "Das Passwort stimmt nicht."
    TEACHER_UNLOCK = "Öffnen"
    TEACHER_INTRO = (
        "Profile auf diesem Computer verwalten. Änderungen gelten sofort. "
        "Der Lernfortschritt auf dem Lernserver bleibt davon unberührt."
    )
    TEACHER_PROFILES_A11Y = "Lernprofile auf diesem Computer"
    TEACHER_PROFILE_ROW = "{pseudonym} · Level {level} · {experience}"
    TEACHER_CURRENT = " (gerade angemeldet)"
    TEACHER_LEVEL = "Freigeschaltetes Level:"
    TEACHER_LEVEL_A11Y = "Freigeschaltetes LearnAgent-Level"
    TEACHER_APPLY_LEVEL = "Level übernehmen"
    TEACHER_RESET = "Fortschritt zurücksetzen"
    TEACHER_DELETE = "Profil löschen"
    TEACHER_CHANGE_PASSWORD = "Passwort ändern …"
    TEACHER_RESET_CONFIRM = (
        "Level, gespeicherten Fortschritt und Kurzanleitung von {pseudonym} zurücksetzen?"
    )
    TEACHER_DELETE_CONFIRM = "Profil {pseudonym} endgültig von diesem Computer löschen?"
    TEACHER_CANNOT_DELETE_CURRENT = (
        "Das gerade angemeldete Profil kann nicht gelöscht werden. Melde dich mit einem "
        "anderen Profil an oder starte LearnHarness neu."
    )
    TEACHER_NO_PROFILES = "Auf diesem Computer gibt es noch keine Profile."

    # Agent changes view and autosave
    CHANGES_TOGGLE = "Änderungen anzeigen"
    CHANGES_TOGGLE_TIP = (
        "Wenn eingeschaltet, siehst du nach dem Schreiben deinen alten und den neuen Code "
        "nebeneinander."
    )
    CHANGES_TITLE = "Das hat sich geändert: {file}"
    CHANGES_INTRO = (
        "Links steht dein alter Code, rechts der neue vom LearnAgent. Rot: entfernt. "
        "Grün: neu. Mit Strg+Z im Editor holst du den alten Code zurück."
    )
    CHANGES_OLD = "Vorher"
    CHANGES_NEW = "Nachher"
    CHANGES_OLD_A11Y = "Alter Code vor dem LearnAgent"
    CHANGES_NEW_A11Y = "Neuer Code vom LearnAgent"
    CHANGES_NEW_FILE = "(Die Datei war vorher leer oder neu.)"
    CHANGES_SUMMARY = "{added} Zeile(n) neu, {removed} Zeile(n) entfernt"
    CHANGES_CLOSE = "Verstanden"
    SETTINGS_EDITOR = "Editor:"
    SETTINGS_AUTOSAVE = "Automatisch speichern (2 Sekunden nach dem Tippen)"
    SETTINGS_LEARNING = "LearnAgent:"
    SETTINGS_SHOW_CHANGES = "Nach dem Schreiben Änderungen anzeigen"
    AUTOSAVED = "Automatisch gespeichert: {file}"

    # Network errors from the learning-server client
    NET_UNREACHABLE = "Der Lernhelfer ist gerade nicht erreichbar."
    NET_TROUBLE = "Der Lernhelfer hat gerade Schwierigkeiten."
    NET_EXCERPT_TOO_LARGE = "Der ausgewählte Codeausschnitt ist zu groß."
    NET_RESPONSE_TOO_LARGE = "Die Serverantwort war zu groß."
    NET_CONNECTION_LOST = "Die Verbindung zum Lernhelfer wurde unterbrochen."
    NET_NO_SESSION = "Es gibt noch keine Lernsitzung."
