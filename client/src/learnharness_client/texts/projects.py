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

    # Project description
    PLAN_HEADING = "Dein Projekt"
    PLAN_INTRO = (
        "Beschreibe, was du bauen möchtest. Der Lernhelfer stellt dir Fragen, damit deine Idee "
        "immer klarer wird. Alle anderen Tabs arbeiten mit deiner Beschreibung."
    )
    PLAN_IDEA_SECTION = "WAS FÜR EIN PROJEKT SOLL DAS WERDEN?"
    PLAN_IDEA_A11Y = "Beschreibung deines Projekts"
    PLAN_IDEA_PLACEHOLDER = "Zum Beispiel: Ein Spiel, in dem ein Fuchs Münzen sammelt."
    PLAN_IDEA_PLACEHOLDER_PYTHON = "Zum Beispiel: Ein Quiz, das mir Mathefragen stellt."
    PLAN_START = "Stell mir Fragen  →"
    PLAN_AGAIN = "Andere Frage"
    PLAN_BUILD = "Los geht's  →"
    PLAN_BUILD_TIP = "Im Tab Missionen baust du dein Projekt Schritt für Schritt."
    PLAN_THINKING = "Der Lernhelfer denkt über dein Projekt nach …"
    PLAN_HELPER_SECTION = "DER LERNHELFER FRAGT"
    PLAN_REPLY_PLACEHOLDER = "Antworte in deinen Worten …"
    PLAN_REPLY_A11Y = "Antwort an den Lernhelfer"
    PLAN_REPLY_SEND = "Antworten"
    PLAN_SUGGESTION_SECTION = "SO KÖNNTE DEINE BESCHREIBUNG JETZT LAUTEN"
    PLAN_ACCEPT = "✓  Übernehmen"
    PLAN_REJECT = "Nein danke"
    PLAN_READY = "Das reicht zum Loslegen! Du kannst aber gern noch mehr erzählen."

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
