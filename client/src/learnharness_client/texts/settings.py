"""Settings and diagnostics."""

from __future__ import annotations

import sys

_WINDOWS = sys.platform == "win32"


class SettingsTexts:
    # Settings
    SETTINGS_TITLE = "Einstellungen"
    SETTINGS_FAKE_SERVER = "Eingebauten Übungsserver verwenden"
    SETTINGS_GODOT_PLACEHOLDER = (
        "Optional, z. B. C:\\Godot\\Godot_v4.exe"
        if _WINDOWS
        else "Optional, z. B. /usr/bin/godot4 – leer: Godot aus dem PATH"
    )
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
    SETTINGS_GODOT_FILTER = "Programme (*.exe);;Alle (*)" if _WINDOWS else "Alle Dateien (*)"
    THEME_SYSTEM = "Wie das System"
    THEME_LIGHT = "Hell"
    THEME_DARK = "Dunkel"
    THEME_HIGH_CONTRAST = "Hoher Kontrast"
    FIRST_START_ADDRESS_A11Y = "Adresse des Lernservers"

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
