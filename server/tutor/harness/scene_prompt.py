"""How the scene of the open script and the input map go out to the AI."""

from __future__ import annotations

from typing import Any

from learnharness_protocol import SceneContext
from learnharness_protocol.scenes import MAX_SCENE_CHANGES, NODE_TYPES

_STR = {"type": "string"}
SCENE_OPS = ["add_node", "set_property", "remove_node", "connect", "disconnect"]

SCENE_CHANGES_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "op": {"type": "string", "enum": SCENE_OPS},
            "parent": _STR,
            "name": _STR,
            "type": _STR,
            "node": _STR,
            "property": _STR,
            "value": _STR,
            "signal": _STR,
            "from": _STR,
            "to": _STR,
            "method": _STR,
        },
        "required": [
            "op", "parent", "name", "type", "node", "property", "value",
            "signal", "from", "to", "method",
        ],
        "additionalProperties": False,
    },
}  # fmt: skip

_FILES_HELP = """<dateien> nennt die Szenen und Skripte des Projekts. Lade mit preload() oder load()
nur Dateien daraus. Braucht der Wunsch oder der Missionsschritt eine Szene, die es noch nicht
gibt (zum Beispiel für einen Gegner), schreibe keinen Code, der sie lädt: Übe einen kleineren
Teil, der ohne sie geht, und sag in "message", welche Szene das Kind zuerst in Godot anlegen
soll, mit Pfad aus dem Bauplan."""

# Read in every prompt with a scene, so chat, hints and reviews understand the block as well.
SCENE_HEADER = (
    "Szene, an der das Skript hängt. Pfade gehen von der Wurzel „.“ aus, $Pfade im Skript vom "
    "Knoten mit „← Skript“. Eine Instanz ist eine eingebettete Szene: Ihre Knoten sind hier "
    "nicht aufgeführt, also behaupte nicht, dass sie fehlen. Fehlen die Schalter autostart, "
    "one_shot, visible, disabled oder monitoring, haben sie den Godot-Standardwert. „(Form "
    "gesetzt)“, „(Bild gesetzt)“ oder „(Ton gesetzt)“ heißt: Das ist in Godot schon eingestellt."
)
# Godot's own ui_* actions are in every project, even when the input map lists none.
ACTIONS_HEADER = (
    "Eigene Aktionen der Input Map. Dazu gibt es in jedem Projekt „ui_left“, „ui_right“, "
    "„ui_up“, „ui_down“, „ui_accept“ und „ui_cancel“."
)
# Talk and code: the files help with wrong preload() paths; explaining and planning the
# project description do not need them.
FILES_INTENTS = ("chat", "review", "learn", "mission", "mission_step")

REVIEW_SCENE_NOTE = """Godot-Projekt: Prüfe auch, ob $Pfade, Signale, Input-Aktionen und geladene
Dateien zu <szene>, <eingaben> und <dateien> passen. <befunde> nennt, was die App im Code und in
der Szene gefunden hat; Befunde zur Szene gelten nur für dieses Skript. Nimm die wichtigsten davon
in deine höchstens zwei Punkte auf. Hat die App mehr gefunden, als du nennst, sag am Ende in einem
Satz, dass im Editor noch weitere Stellen markiert sind. Ein Problem in der Szene, zum Beispiel ein
Timer, der nie startet, hat keine Zeile im Code: Nenne dann den Knoten und wo das Kind es in Godot
ändert (Inspektor, Knoten → Signale oder Projekt → Projekteinstellungen → Eingabe-Zuordnung).
"marked_lines" enthält nur Zeilen aus <code>."""

EXPLAIN_SCENE_NOTE = """Godot-Projekt: Erkläre, wenn es hilft, wie der Code mit <szene>
zusammenhängt: welches Signal eine Funktion aufruft und welcher Knoten hinter einem $Pfad steht.
Die Verständnisfrage darf auch einen Wert aus der Szene verändern, zum Beispiel „Was passiert,
wenn wait_time 5 statt 2 ist?“."""

CHAT_SCENE_NOTE = """Hier änderst du weder Code noch Szene. Fehlt in <szene> ein Knoten, erkläre,
wie das Kind ihn in Godot anlegt, oder nenne den LearnAgent oder eine Mission: Dort ergänzt die
App ihn nach einer richtigen Antwort selbst."""

SCENE_HELP = (
    f"""Szene: Nutze in "new_file_content" nur Knoten aus <szene> oder aus deinen
"scene_changes" und nur Aktionen aus <eingaben> oder die immer vorhandenen ui_-Aktionen. Knoten
innerhalb einer Instanz nutzt und änderst du nicht, sondern sprichst die Instanz selbst an.

Gehört der Wunsch oder der Missionsschritt nicht in diese Szene (ein Gegner-Erzeuger gehört zum
Beispiel in die Hauptszene, nicht in die Spielfigur), ändere diese Szene nicht. Übe dann einen
Teil, der in dieses Skript passt, und nenne in "message" die richtige Datei.

Braucht der neue Code einen Knoten, einen Wert oder ein Signal, das es in der Szene noch nicht
gibt, ergänze es in "scene_changes" (höchstens {MAX_SCENE_CHANGES} Einträge, sonst eine leere
Liste). Jeder Eintrag hat alle Felder, nicht benötigte bleiben leer:
- "add_node": "parent" (Pfad), "name" (nur Buchstaben, Ziffern, _), "type" (z. B. Timer, Area2D,
  CollisionShape2D, Sprite2D, Label, Button, AudioStreamPlayer).
- "set_property": "node" (Pfad), "property" (z. B. wait_time, position, text), "value" als
  einfacher Godot-Wert: 2.0, true, "Text", Vector2(10, 20), Color(1, 0, 0, 1). Für "shape" einer
  CollisionShape2D: RectangleShape2D(size=Vector2(32, 32)) oder CircleShape2D(radius=16).
- "remove_node": "node" (Pfad, nicht die Wurzel und nicht der Knoten mit dem Skript).
- "connect" / "disconnect": "signal", "from" (Pfad des Senders), "to" (Pfad des Empfängers),
  "method". Führt "to" zum Knoten mit dem Skript, steht func <method>(…) in "new_file_content".
Lücken der Übung stehen nur im Code, nie in "scene_changes".
Ein neuer Knoten bekommt seine Werte mit "set_property" auf seinem neuen Pfad. Ändere nur, was
die Übung braucht. Signale aus der Szene verbindest du mit "connect", nicht im Code mit
connect(). Damit ein neuer Knoten wirkt:
- Ein Timer braucht "autostart" = true oder $Name.start() im Code.
- Eine neue CollisionShape2D braucht "shape". Eine schon gesetzte Form bleibt unverändert.
- Bilder, Töne und Schriften (texture, stream, font) setzt du nicht: Sag in "message", wo das
  Kind sie in Godot im Inspektor einstellt.
Ausnahme von den Themen des Kindes: Eine Methode, die du mit "connect" an ein Signal hängst,
darfst du schreiben, auch wenn das Kind Funktionen noch nicht kennt. Erkläre sie in einem
Kommentar darüber und mach sie nicht zum Thema der Übung.
Erlaubte Knotentypen: {", ".join(sorted(NODE_TYPES))}.

"""
    + _FILES_HELP
)

NO_SCENE_HELP = (
    """Zu diesem Skript ist keine Szene bekannt. Erfinde in "new_file_content" keine
Knoten mit $ oder get_node und nutze nur Aktionen aus <eingaben> oder die immer vorhandenen
ui_-Aktionen.

"""
    + _FILES_HELP
)


NO_CODE_STEP_NOTE = """In diesem Schritt ändert die App weder den Code noch die Szene. Versprich
keine Änderung, sondern erkläre nur, was in <szene> schon da ist oder später dazukommt."""

MISSION_FILES_NOTE = """Godot-Projekt: <dateien> nennt die Szenen und Skripte des Projekts. Gibt
es <szene>, ist das die Szene des Skripts aus der Zeile „Datei:“: Plane dann nur Bausteine, die
in diese Szene passen.

Gehört der ganze Wunsch oder der ganze nächste Baustein in ein anderes Skript aus <dateien> (ein
Gegner-Erzeuger gehört zum Beispiel in die Hauptszene, nicht in die Spielfigur), trage dessen Pfad
in "open_file" ein. Hat die passende Szene noch kein Skript (keine .gd-Datei in ihrem Ordner),
trage stattdessen den Pfad der Szene ein. In beiden Fällen gibt es keinen Plan, und die übrigen
Felder werden nicht beachtet. Sonst bleibt "open_file" leer.

Fehlt für den Baustein eine Szene (zum Beispiel für einen Gegner) oder eine Taste, die nicht in
<eingaben> steht, plane nur, was ohne sie geht. Sag dann in "message" im zweiten Satz, was
das Kind zuerst in Godot anlegen soll: eine Szene mit Pfad aus dem Bauplan oder eine Aktion unter
Projekt → Projekteinstellungen → Eingabe-Zuordnung.

Knoten in der Szene aus <szene>, zum Beispiel einen Timer, ergänzt die App in einem
"exercise"-Schritt selbst. Plane dafür keinen eigenen Schritt.

Ein Timer oder Signal, das etwas wiederholt, ist keine Schleife: Wähle das Thema nach dem Code,
den das Kind schreibt, zum Beispiel variables für einen Zähler.

Ausnahme von den Themen des Kindes: Eine Methode, die auf ein Signal reagiert (zum Beispiel wenn
ein Timer abläuft), darf vorkommen, auch wenn das Kind Funktionen noch nicht kennt. Sie ist
Gerüst und nicht Thema der Mission."""


def scene_help(scene: SceneContext | None) -> str:
    return SCENE_HELP if scene is not None else NO_SCENE_HELP


def with_scene_changes(schema: dict[str, Any]) -> dict[str, Any]:
    """The exercise format plus the scene changes, still strict."""
    properties = {**schema["properties"], "scene_changes": SCENE_CHANGES_SCHEMA}
    return {**schema, "properties": properties, "required": list(properties)}


def files_text(files: list[str]) -> str:
    return "\n".join("res://" + path.lstrip("/") for path in files) or "(keine)"


def scene_tree_text(scene: SceneContext) -> str:
    """The scene as an indented tree the AI can read like the Godot scene panel."""
    lines = [f"Datei: {scene.path}"]
    for node in scene.nodes:
        depth = 0 if node.path == "." else node.path.count("/") + 1
        root = f"{scene.root_name} (Wurzel)" if scene.root_name else "(Wurzel)"
        name = node.path.rsplit("/", 1)[-1] if node.path != "." else root
        kind = node.type or (f"Instanz von {node.instance}" if node.instance else "?")
        text = f"{'  ' * depth}- {name} ({kind})"
        if "/" in node.path:
            text += f" [Pfad: {node.path}]"
        if node.path == scene.script_node:
            text += " ← Skript"
        values = ", ".join(f"{key} = {value}" for key, value in node.properties.items())
        if values:
            text += f" {{{values}}}"
        lines.append(text)
    if scene.connections:
        root = scene.root_name or "(Wurzel)"

        def node(path: str) -> str:
            return root if path == "." else path

        lines.append("Signale:")
        lines += [
            f"- {node(item.from_node)}.{item.signal} → {node(item.to_node)}.{item.method}()"
            for item in scene.connections
        ]
    return "\n".join(lines)
