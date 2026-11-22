"""Demo project-plan answers."""

from __future__ import annotations

PLAN_FIRST_QUESTION = "Tolle Idee! Was ist das Wichtigste, das dein Projekt zuerst können soll?"


PLAN_FOLLOW_UP = "Gut überlegt! Welchen Schritt möchtest du als Nächstes angehen?"


PLAN_STEPS: dict[str, tuple[str, ...]] = {
    "gdscript": (
        "Die Spielfigur in einer Szene anlegen",
        "Die Figur mit den Pfeiltasten bewegen",
        "Etwas zum Einsammeln ins Spiel setzen",
        "Punkte zählen und anzeigen",
        "Ein Ziel oder Ende für das Spiel bauen",
        "Freunde testen lassen und verbessern",
    ),
    "python": (
        "Aufschreiben, was das Programm am Anfang anzeigt",
        "Eine Eingabe vom Menschen abfragen",
        "Mit einer Bedingung auf die Eingabe reagieren",
        "Das Ergebnis schön anzeigen",
        "Das Programm in einer Schleife wiederholen",
        "Jemanden testen lassen und verbessern",
    ),
}
