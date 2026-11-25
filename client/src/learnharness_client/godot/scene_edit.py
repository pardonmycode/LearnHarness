"""Applies checked scene changes to the text of a Godot 4 scene.

Only the sections a change means are touched. Every step is checked again here, because a
broken scene would stop the child's whole game from opening.
"""

from __future__ import annotations

import re
import secrets

from learnharness_protocol import (
    AddNode,
    ConnectSignal,
    DisconnectSignal,
    RemoveNode,
    SceneChange,
    SetProperty,
)
from learnharness_protocol.scenes import value_problem

from .scene_file import PROPERTY_LINE, ParsedScene, Section, parse_header, parse_scene

_SHAPE = re.compile(r"^(\w+)\((.*)\)$")


class SceneEditError(ValueError):
    """The change does not fit this scene; nothing was changed."""


def _quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _section(text: str) -> Section:
    lines = text.splitlines(keepends=True)
    header = parse_header(lines[0])
    assert header is not None
    return Section(header[0], header[1], lines)


def _ensure_gap(section: Section) -> None:
    """A blank line after a section, as Godot writes it."""
    if not section.lines[-1].endswith("\n"):
        section.lines[-1] += "\n"
    if section.lines[-1].strip():
        section.lines.append("\n")


def _subtree(scene: ParsedScene, path: str) -> list[Section]:
    prefix = "" if path == "." else path + "/"
    return [n.section for n in scene.nodes if n.path == path or n.path.startswith(prefix)]


def _touches(section: Section, path: str) -> bool:
    return any(_inside(section.attr(end) or "", path) for end in ("from", "to"))


def _new_id(scene: ParsedScene, kind: str) -> str:
    used = {section.attr("id") for section in scene.sections}
    while True:
        candidate = f"{kind}_lh{secrets.token_hex(3)}"
        if candidate not in used:
            return candidate


def _add_shape(scene: ParsedScene, value: str) -> str:
    match = _SHAPE.match(value)
    if match is None:
        raise SceneEditError("Form unbekannt")
    kind, arguments = match.groups()
    resource_id = _new_id(scene, kind)
    body = [
        f"{key} = {raw}\n" for key, raw in re.findall(r"(\w+)=(\w+\([^)]*\)|[-\d.e]+)", arguments)
    ]
    section = _section(f"[sub_resource type={_quote(kind)} id={_quote(resource_id)}]\n")
    section.lines += [*body, "\n"]
    first_node = next(i for i, s in enumerate(scene.sections) if s.kind == "node")
    _ensure_gap(scene.sections[first_node - 1])
    scene.sections.insert(first_node, section)
    _count_load_step(scene)
    return f'SubResource("{resource_id}")'


def _count_load_step(scene: ParsedScene) -> None:
    header = scene.sections[0]
    steps = header.attributes.get("load_steps")
    if steps is not None and steps.isdigit():
        header.lines[0] = header.lines[0].replace(
            f"load_steps={steps}", f"load_steps={int(steps) + 1}", 1
        )
        header.attributes["load_steps"] = str(int(steps) + 1)


def _add_node(scene: ParsedScene, change: AddNode) -> None:
    parent = scene.node(change.parent)
    if parent is None:
        raise SceneEditError(f"Elternknoten {change.parent} fehlt")
    path = change.name if change.parent == "." else f"{change.parent}/{change.name}"
    if scene.node(path) is not None:
        raise SceneEditError(f"Knoten {path} gibt es schon")
    header = (
        f"[node name={_quote(change.name)} type={_quote(change.type)} "
        f"parent={_quote(change.parent)}]\n"
    )
    last = _subtree(scene, change.parent)[-1]
    index = scene.sections.index(last) + 1
    _ensure_gap(last)
    scene.sections.insert(index, _section(header + "\n"))


def _set_property(scene: ParsedScene, change: SetProperty) -> None:
    node = scene.node(change.node)
    if node is None:
        raise SceneEditError(f"Knoten {change.node} fehlt")
    problem = value_problem(change.property, change.value)
    if problem:
        raise SceneEditError(problem)
    value = _add_shape(scene, change.value) if change.property == "shape" else change.value
    section = node.section
    body_end = len(section.body()) + 1
    start = next(
        (
            i
            for i in range(1, body_end)
            if (m := PROPERTY_LINE.match(section.lines[i])) and m.group(1) == change.property
        ),
        None,
    )
    line = f"{change.property} = {value}\n"
    if start is None:
        section.lines.insert(body_end, line)
        return
    end = start + 1  # a value over several lines ends at the next property
    while end < body_end and not PROPERTY_LINE.match(section.lines[end]):
        end += 1
    section.lines[start:end] = [line]


def _remove_node(scene: ParsedScene, change: RemoveNode) -> None:
    if change.node == "." or scene.node(change.node) is None:
        raise SceneEditError(f"Knoten {change.node} kann nicht entfernt werden")
    gone = {id(section) for section in _subtree(scene, change.node)}
    scene.sections = [
        section
        for section in scene.sections
        if id(section) not in gone
        and not (section.kind == "connection" and _touches(section, change.node))
        and not (section.kind == "editable" and _inside(section.attr("path") or "", change.node))
    ]


def _inside(path: str, node: str) -> bool:
    return path == node or path.startswith(node + "/")


def _find_connection(
    scene: ParsedScene, change: ConnectSignal | DisconnectSignal
) -> Section | None:
    wanted = (change.signal, change.from_node, change.to_node, change.method)
    return next(
        (
            section
            for section in scene.connections()
            if (section.attr("signal"), section.attr("from"), section.attr("to"),
                section.attr("method")) == wanted
        ),
        None,
    )  # fmt: skip


def _connect(scene: ParsedScene, change: ConnectSignal) -> None:
    for end in (change.from_node, change.to_node):
        if scene.node(end) is None:
            raise SceneEditError(f"Knoten {end} fehlt")
    if _find_connection(scene, change) is not None:
        raise SceneEditError("Signal ist schon verbunden")
    header = (
        f"[connection signal={_quote(change.signal)} from={_quote(change.from_node)} "
        f"to={_quote(change.to_node)} method={_quote(change.method)}]\n"
    )
    last = scene.sections[-1]
    if last.kind == "connection":
        if not last.lines[-1].endswith("\n"):
            last.lines[-1] += "\n"
    else:
        _ensure_gap(last)
    scene.sections.append(_section(header))


def _disconnect(scene: ParsedScene, change: DisconnectSignal) -> None:
    section = _find_connection(scene, change)
    if section is None:
        raise SceneEditError("Diese Signalverbindung gibt es nicht")
    scene.sections.remove(section)


def apply_scene_changes(text: str, changes: list[SceneChange]) -> str:
    """The new scene text, or SceneEditError when any step does not fit."""
    for change in changes:
        scene = parse_scene(text)
        if scene is None or not scene.nodes:
            raise SceneEditError("Keine Godot-4-Szene")
        if isinstance(change, AddNode):
            _add_node(scene, change)
        elif isinstance(change, SetProperty):
            _set_property(scene, change)
        elif isinstance(change, RemoveNode):
            _remove_node(scene, change)
        elif isinstance(change, ConnectSignal):
            _connect(scene, change)
        else:
            _disconnect(scene, change)
        text = scene.text()  # parsed again, so the next step sees the new nodes
    if parse_scene(text) is None:
        raise SceneEditError("Szene wäre danach kaputt")
    return text
