"""Checks scene changes from the AI and plays them through on the node list."""

from __future__ import annotations

import re
from typing import Any

from learnharness_protocol import (
    AddNode,
    ConnectSignal,
    DisconnectSignal,
    RemoveNode,
    SceneChange,
    SceneContext,
    SceneEdit,
    SetProperty,
)
from learnharness_protocol.scenes import MAX_SCENE_CHANGES
from pydantic import TypeAdapter, ValidationError

from .errors import HarnessRejected
from .scene_code import check_code_uses_scene, check_loaded_files, inside

_FIELDS = {
    "add_node": ("parent", "name", "type"),
    "set_property": ("node", "property", "value"),
    "remove_node": ("node",),
    "connect": ("signal", "from", "to", "method"),
    "disconnect": ("signal", "from", "to", "method"),
}
_RENAMED = {"from": "from_node", "to": "to_node"}
# Signals of common nodes: a wrong name would only show up as an error in Godot.
_COMMON = {"ready", "tree_entered", "tree_exited", "visibility_changed"}
_AREA = {"body_entered", "body_exited", "area_entered", "area_exited", "input_event"}
_AREA |= {"mouse_entered", "mouse_exited"}
_BUTTON = {"pressed", "toggled", "button_down", "button_up", "mouse_entered", "mouse_exited"}
SIGNALS: dict[str, set[str]] = {
    "Timer": {"timeout"},
    "Button": _BUTTON,
    "CheckBox": _BUTTON,
    "Area2D": _AREA,
    "Area3D": _AREA,
    "VisibleOnScreenNotifier2D": {"screen_entered", "screen_exited"},
    "AnimationPlayer": {"animation_finished", "animation_started"},
    "AnimatedSprite2D": {"animation_finished", "animation_looped", "frame_changed"},
    "LineEdit": {"text_changed", "text_submitted"},
    "AudioStreamPlayer": {"finished"},
    "AudioStreamPlayer2D": {"finished"},
}
_ADAPTER: TypeAdapter[SceneChange] = TypeAdapter(SceneChange)


def parse_scene_changes(items: Any) -> list[SceneChange]:
    """The AI's flat entries as protocol changes; empty fields are left out."""
    if not isinstance(items, list):
        return []
    if len(items) > MAX_SCENE_CHANGES:
        raise HarnessRejected(f"Mehr als {MAX_SCENE_CHANGES} Szenenänderungen")
    changes: list[SceneChange] = []
    for item in items:
        op = str(item.get("op", "")) if isinstance(item, dict) else ""
        if op not in _FIELDS:
            raise HarnessRejected(f"Unbekannte Szenenänderung „{op}“")
        data = {_RENAMED.get(key, key): str(item.get(key, "")).strip() for key in _FIELDS[op]}
        try:
            changes.append(_ADAPTER.validate_python({"op": op, **data}))
        except ValidationError as exc:
            problem = exc.errors()[0].get("msg", "ungültig")
            raise HarnessRejected(f"Szenenänderung {op} abgelehnt: {problem}") from exc
    return changes


def _method_defined(code: str, method: str) -> bool:
    return re.search(rf"^\s*func\s+{re.escape(method)}\s*\(", code, re.MULTILINE) is not None


def check_scene_changes(scene: SceneContext, changes: list[SceneChange], code: str) -> str | None:
    """Plays the changes through on the node list; a reason if one does not fit."""
    types = {node.path: node.type for node in scene.nodes}
    instances = {node.path for node in scene.nodes if node.instance}
    shapes = {node.path: node.properties for node in scene.nodes}
    links = {(c.signal, c.from_node, c.to_node, c.method) for c in scene.connections}
    for change in changes:
        if isinstance(change, AddNode):
            path = change.name if change.parent == "." else f"{change.parent}/{change.name}"
            if change.parent not in types:
                return f"Elternknoten {change.parent} gibt es nicht"
            if change.parent in instances:
                return f"In die Instanz {change.parent} kommen keine neuen Knoten"
            if path in types:
                return f"Knoten {path} gibt es schon"
            types[path] = change.type
        elif isinstance(change, SetProperty):
            if change.node not in types:
                return f"Knoten {change.node} gibt es nicht"
            if change.property == "shape" and "shape" in shapes.get(change.node, {}):
                return f"Knoten {change.node} hat schon eine Form; die bleibt unverändert"
        elif isinstance(change, RemoveNode):
            if change.node not in types or inside(scene.script_node, change.node):
                return f"Knoten {change.node} darf nicht entfernt werden"
            types = {p: t for p, t in types.items() if not inside(p, change.node)}
            links = {
                link for link in links if not any(inside(end, change.node) for end in link[1:3])
            }
        else:
            key = (change.signal, change.from_node, change.to_node, change.method)
            if isinstance(change, DisconnectSignal):
                if key not in links:
                    return "Diese Signalverbindung gibt es nicht"
                links.discard(key)
                continue
            assert isinstance(change, ConnectSignal)
            for end in (change.from_node, change.to_node):
                if end not in types:
                    return f"Knoten {end} gibt es nicht"
            known = SIGNALS.get(types[change.from_node])
            if known is not None and change.signal not in known | _COMMON:
                return f"{types[change.from_node]} hat kein Signal {change.signal}"
            if key in links:
                return "Signal ist schon verbunden"
            if change.to_node == scene.script_node and not _method_defined(code, change.method):
                return f"func {change.method}() fehlt im Code"
            links.add(key)
    return _new_nodes_work(changes, code)


def _new_nodes_work(changes: list[SceneChange], code: str) -> str | None:
    """A new Timer that never starts or a shape without a form would silently do nothing."""
    values = {
        (change.node, change.property): change.value
        for change in changes
        if isinstance(change, SetProperty)
    }
    for change in changes:
        if not isinstance(change, AddNode):
            continue
        path = change.name if change.parent == "." else f"{change.parent}/{change.name}"
        if change.type == "Timer":
            started = re.search(rf"\b{re.escape(change.name)}\.start\(", code) is not None
            if values.get((path, "autostart")) != "true" and not started:
                return f"Timer {path} startet nie (autostart = true oder start() fehlt)"
        if (
            change.type in ("CollisionShape2D", "CollisionShape3D")
            and (path, "shape") not in values
        ):
            return f"{change.type} {path} hat keine Form (shape fehlt)"
    return None


def checked_scene_changes(
    scene: SceneContext | None,
    actions: list[str],
    files: list[str],
    items: Any,
    before: str,
    after: str,
) -> list[SceneChange]:
    """The scene changes of an exercise, after every check; HarnessRejected otherwise."""
    changes = parse_scene_changes(items) if scene is not None else []
    reason = check_scene_changes(scene, changes, after) if scene is not None else None
    reason = reason or check_code_uses_scene(scene, actions, changes, before, after)
    reason = reason or check_loaded_files(files, before, after)
    if reason:
        raise HarnessRejected(f"Code passt nicht zu Szene oder Projekt: {reason}")
    return changes


def scene_preview(scene: SceneContext | None, changes: list[SceneChange]) -> SceneEdit | None:
    """Shown before the answer: which nodes and signals the scene will get."""
    if scene is None or not changes:
        return None
    return SceneEdit(path=scene.path, changes=changes, explanation=SCENE_EXPLANATION)


SCENE_EXPLANATION = "Neue Knoten und Signale für deine Szene."
