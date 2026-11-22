"""First start, tutorial and login."""

from __future__ import annotations


class OnboardingTexts:
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
            "1. Dein Projekt",
            "Links siehst du deine Skripte für Godot oder Python. Mit einem Doppelklick "
            "öffnest du eins. Mit Strg+S speicherst du.",
        ),
        (
            "2. Der LearnAgent",
            "Rechts beschreibst du, was dein Projekt können soll. Der Agent stellt dir zuerst "
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

    # Login
    LOGIN_TITLE = "Wer programmiert heute?"
    LOGIN_HEADING = "Willkommen in der Programmierwerkstatt!"
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
