"""Errors from the domain and network layers."""

from __future__ import annotations


class ErrorTexts:
    # Domain errors (shown to the child via QMessageBox)
    PATH_NOT_PROJECT = "Der gewählte Ordner ist kein Godot-Projekt."
    PATH_LINKED = "Verknüpfte Ordner und Dateien sind hier nicht erlaubt."
    PATH_PROTECTED = "Dieser Projektordner ist geschützt."
    PATH_ADDONS = "Add-ons sind standardmäßig ausgeblendet."
    PATH_GDIGNORE = "Dieser Ordner wird von Godot ignoriert."
    PATH_OUTSIDE = "Die Datei liegt außerhalb des Projekts."
    PATH_NOT_FOUND = "Die Skriptdatei wurde nicht gefunden."
    PATH_ONLY_GD = "In einem Godot-Projekt dürfen nur GDScript-Dateien geöffnet werden."
    PATH_ONLY_PY = "In einem Python-Projekt dürfen nur Python-Dateien geöffnet werden."
    PATH_NOT_FILE = "Der Pfad ist keine Skriptdatei."
    PROJECT_MISSING_DESCRIPTOR = (
        "In diesem Ordner habe ich kein Godot-Projekt (project.godot) und keine Python-Datei "
        "gefunden."
    )
    PROJECT_FOLDER_TOO_BROAD = (
        "Dieser Ordner ist zu groß für ein Projekt. Lege dein Skript in einen eigenen Ordner."
    )
    PROJECT_NAME_INVALID = (
        "Der Name darf Buchstaben, Zahlen, Leerzeichen, - und _ enthalten (höchstens 60 Zeichen)."
    )
    PROJECT_EXISTS = "Einen Ordner mit diesem Namen gibt es dort schon."
    FILE_TOO_LARGE = "Diese Datei ist zu groß für den Lerneditor."
    FILE_NOT_UTF8 = "Die Datei ist nicht als UTF-8 gespeichert."
    FILE_CHANGED_ON_DISK = "Die Datei wurde seit dem Öffnen in einem anderen Programm geändert."
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

    # Network errors from the learning-server client
    NET_UNREACHABLE = "Der Lernhelfer ist gerade nicht erreichbar."
    NET_TROUBLE = "Der Lernhelfer hat gerade Schwierigkeiten."
    NET_EXCERPT_TOO_LARGE = "Der ausgewählte Codeausschnitt ist zu groß."
    NET_RESPONSE_TOO_LARGE = "Die Serverantwort war zu groß."
    NET_CONNECTION_LOST = "Die Verbindung zum Lernhelfer wurde unterbrochen."
    NET_NO_SESSION = "Es gibt noch keine Lernsitzung."
