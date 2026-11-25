"""Godot scenes: the node tree and changes made by the learning helper."""

from __future__ import annotations


class SceneTexts:
    SCENE_TREE = "Szene"
    SCENE_TREE_A11Y = "Knoten der Szene zum offenen Skript"
    SCENE_NONE = "Keine Szene zu diesem Skript"
    SCENE_OLD_FORMAT = "Nur Szenen aus Godot 4 werden angezeigt"
    SCENE_FILE = "Szene: {file}"
    SCENE_NODE = "{name} ({type})"
    SCENE_INSTANCE = "Szene {file}"
    SCENE_SCRIPT_MARK = "  ← dein Skript"
    SCENE_SIGNALS = "Signale"
    SCENE_SIGNAL = "{signal} → {method}()"
    SCENE_NEW = "neu"
    SCENE_REMOVED = "wird entfernt"
    SCENE_CHANGED = "{property} = {value}"
    SCENE_PREVIEW_TIP = "Das kommt nach der richtigen Antwort in deine Szene."
    SCENE_WRITTEN = (
        "Szene {file} geändert. Ist sie in Godot offen? Dann wähle dort "
        "„Szene → Gespeicherte Szene neu laden“, sonst überschreibt Godot die Änderung."
    )
    SCENE_NOT_WRITTEN_TITLE = "Szene nicht geändert"
    SCENE_CHANGED_MEANWHILE = (
        "Die Szene {file} wurde inzwischen geändert. Damit nichts kaputtgeht, habe ich weder "
        "die Szene noch den Code geändert. Starte die Übung einfach noch einmal."
    )
    SCENE_DOES_NOT_FIT = (
        "Die Änderung passt nicht zur Szene {file}. Ich habe weder die Szene noch den Code "
        "geändert."
    )
    SCENE_WRITE_FAILED = "Die Szene {file} konnte nicht gespeichert werden: {error}"
