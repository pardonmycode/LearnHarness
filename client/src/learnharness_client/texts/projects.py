"""Project choice, project plan and agent changes."""

from __future__ import annotations


class ProjectTexts:
    # Project choice
    PROJECT_CHOICE_TITLE = "Welches Projekt möchtest du bearbeiten?"
    PROJECT_CHOICE_INTRO = "Diese Projekte habe ich auf deinem Computer gefunden. Wähle eins aus."
    PROJECT_CHOICE_LIST_A11Y = "Gefundene Projekte"
    PROJECT_CHOICE_RECENT_TAG = "Zuletzt benutzt · {path}"
    PROJECT_CHOICE_GODOT_TAG = "Aus Godot · {path}"
    PROJECT_CHOICE_OPEN = "Öffnen"
    PROJECT_CHOICE_OTHER_FOLDER = "Anderen Ordner wählen …"
    PROJECT_CHOICE_CANCEL = "Abbrechen"

    # Project plan
    PLAN_HEADING = "Dein Projekt"
    PLAN_INTRO = (
        "Beschreibe, was du bauen möchtest. Der Lernhelfer fragt nach und schlägt Schritte vor. "
        "Du entscheidest, was auf deine To-do-Liste kommt. Deine Idee hilft ihm auch in den "
        "anderen Tabs."
    )
    PLAN_IDEA_SECTION = "WAS FÜR EIN PROJEKT SOLL DAS WERDEN?"
    PLAN_IDEA_A11Y = "Beschreibung deines Projekts"
    PLAN_IDEA_PLACEHOLDER = "Zum Beispiel: Ein Spiel, in dem ein Fuchs Münzen sammelt."
    PLAN_IDEA_PLACEHOLDER_PYTHON = "Zum Beispiel: Ein Quiz, das mir Mathefragen stellt."
    PLAN_START = "Gemeinsam planen  →"
    PLAN_AGAIN = "Neue Vorschläge holen"
    PLAN_THINKING = "Der Lernhelfer denkt über dein Projekt nach …"
    PLAN_HELPER_SECTION = "DER LERNHELFER"
    PLAN_REPLY_PLACEHOLDER = "Antworte dem Lernhelfer …"
    PLAN_REPLY_A11Y = "Antwort an den Lernhelfer"
    PLAN_REPLY_SEND = "Antworten"
    PLAN_ACCEPT = "Auf die Liste"
    PLAN_ACCEPT_A11Y = "{todo} auf die Liste setzen"
    PLAN_REJECT = "Nein danke"
    PLAN_REJECT_A11Y = "{todo} nicht übernehmen"
    PLAN_ACCEPT_ALL = "Alle auf die Liste"
    PLAN_TODO_SECTION = "DEINE TO-DO-LISTE"
    PLAN_TODO_A11Y = "To-do-Liste. Leertaste hakt ab, F2 ändert den Text."
    PLAN_ADD_PLACEHOLDER = "Eigenes To-do hinzufügen …"
    PLAN_ADD_A11Y = "Neues To-do"
    PLAN_ADD = "Hinzufügen"
    PLAN_MOVE_UP = "↑"
    PLAN_MOVE_UP_A11Y = "To-do nach oben schieben"
    PLAN_MOVE_DOWN = "↓"
    PLAN_MOVE_DOWN_A11Y = "To-do nach unten schieben"
    PLAN_REMOVE = "Entfernen"
    PLAN_EMPTY = "Noch keine To-dos."
    PLAN_PROGRESS = "{done} von {total} erledigt"
    PLAN_ALL_DONE = "Alles erledigt! 🎉"
    PLAN_LIST_FULL = "Deine Liste ist voll ({count} To-dos). Entferne zuerst eins."
    PLAN_ALREADY_LISTED = "Das steht schon auf deiner Liste."

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
