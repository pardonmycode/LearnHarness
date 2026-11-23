"""Editor, conflicts, versions, script tree and problems."""

from __future__ import annotations


class EditorTexts:
    # Conflict and recovery dialogs
    CONFLICT_TITLE = "Die Datei wurde auch woanders geändert"
    CONFLICT_INTRO = (
        "Deine Version und die Version auf der Festplatte sind verschieden. "
        "Wähle bewusst, welche Version du behalten möchtest."
    )
    CONFLICT_DISK_VERSION = "Version auf der Festplatte"
    CONFLICT_MY_VERSION = "Meine Version"
    CONFLICT_SAME = "Die Texte sehen gleich aus."
    CONFLICT_KEEP_MINE = "Meine Version behalten"
    CONFLICT_LOAD_DISK = "Version von der Festplatte laden"
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
    FILE_TOO_LONG_TITLE = "Dieses Skript ist sehr lang"
    FILE_TOO_LONG = (
        "Damit nichts von deinem Code verloren geht, schreibt der Lernhelfer hier nichts hinein. "
        "Deine Antwort zählt trotzdem. Baue die Lösung selbst ein oder teile dein Skript in "
        "kleinere Dateien auf."
    )
    FILE_CHANGED_TITLE = "Dein Skript hat sich geändert"
    FILE_CHANGED = (
        "Du hast dein Skript verändert, während die Übung offen war. Damit deine Änderung "
        "erhalten bleibt, schreibt der Lernhelfer nichts hinein. Deine Antwort zählt trotzdem. "
        "Baue die Lösung selbst ein oder starte eine neue Runde."
    )
    SAVED = "Gespeichert: {file}"
    SAVE_FAILED_TITLE = "Speichern nicht möglich"
    SAVE_FAILED = "Dein Text bleibt im Editor und wurde als Entwurf gesichert.\n\n{error}"
    RELOADED_FROM_DISK = "Neu geladen: {file}"
    DELETED_EXTERNALLY = "{file} wurde außerhalb des Editors gelöscht. Dein Text bleibt geöffnet."
    KEEPING_MY_VERSION = "Deine Version bleibt im Editor. Speichere sie bewusst mit Strg+S."
    UNSAVED_CHANGES_TITLE = "Ungespeicherte Änderungen"
    UNSAVED_CHANGES = "Möchtest du {file} vor dem Schließen speichern?"

    # Script tree
    SCRIPTS = "Skripte"
    SCRIPTS_A11Y = "Skriptdateien im Projekt"

    # Problems
    PROBLEM_INPUT_PLACEHOLDER = "Godot-Fehlermeldung hier einfügen …"
    PROBLEM_INPUT_A11Y = "Godot-Fehlermeldung einfügen"
    PROBLEM_INPUT_PLACEHOLDER_PYTHON = "Python-Fehlermeldung hier einfügen …"
    PROBLEM_INPUT_A11Y_PYTHON = "Python-Fehlermeldung einfügen"
    PROBLEM_ADD = "Fehler hinzufügen"
    PROBLEM_LIST_A11Y = "Liste der Probleme"
    SOURCE_GODOT = "Godot"
    SOURCE_GODOT_CHECK = "Godot-Prüfung"
    SOURCE_GODOT_LOG = "Godot-Log"
    SOURCE_PYTHON = "Python"
    SOURCE_PYTHON_CHECK = "Python-Prüfung"
    SOURCE_REVIEW = "Prüfung"

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

    # Backup dialog details
    BACKUP_LIST_A11Y = "Liste der älteren Versionen"
    BACKUP_PREVIEW_A11Y = "Inhalt der ausgewählten älteren Version"
    BACKUP_UNREADABLE = "(Diese Sicherung kann nicht gelesen werden: {error})"
    BACKUP_TODAY = "Heute, {time} Uhr"
    BACKUP_DATE = "{date} Uhr"
