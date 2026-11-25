"""Reads Godot 4 scene files (.tscn, format=3) without changing a single character.

A scene is kept as a list of sections with their original text, so a later edit can touch
exactly the sections it means and leave everything else as Godot wrote it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_HEADER = re.compile(r"^\[(\w+)((?:\s+[^\]]*)?)\]\s*$")
_ATTRIBUTE = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|\w+\("(?:[^"\\]|\\.)*"\)|[^\s\]]+)')
_REFERENCE = re.compile(r'^(?:Ext|Sub)Resource\("((?:[^"\\]|\\.)*)"\)$')
PROPERTY_LINE = re.compile(r"^([A-Za-z_][\w/]*) = ")
MAX_SCENE_BYTES = 512_000
MAX_CONTEXT_VALUE = 60


def _unquote(value: str) -> str:
    if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
        return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return value


def reference_id(value: str) -> str | None:
    """The id inside ExtResource("…") or SubResource("…")."""
    match = _REFERENCE.match(value.strip())
    return match.group(1) if match else None


@dataclass
class Section:
    kind: str  # gd_scene, ext_resource, sub_resource, node, connection, editable
    attributes: dict[str, str]  # raw values, strings still quoted
    lines: list[str]  # header first, then properties; trailing blank lines included

    def attr(self, name: str) -> str | None:
        raw = self.attributes.get(name)
        return None if raw is None else _unquote(raw)

    def body(self) -> list[str]:
        """Property lines without the header and the blank lines at the end."""
        end = len(self.lines)
        while end > 1 and not self.lines[end - 1].strip():
            end -= 1
        return self.lines[1:end]

    def properties(self) -> dict[str, str]:
        found: dict[str, str] = {}
        last: str | None = None
        for line in self.body():
            match = PROPERTY_LINE.match(line)
            if match:
                last = match.group(1)
                found[last] = line[match.end() :].rstrip("\n")
            elif last is not None:  # a value over several lines, e.g. a dictionary
                found[last] += "\n" + line.rstrip("\n")
        return found


@dataclass
class SceneNodeInfo:
    path: str
    type: str
    instance: str | None
    script: str | None
    properties: dict[str, str]
    section: Section


@dataclass
class ParsedScene:
    preamble: list[str]
    sections: list[Section]
    nodes: list[SceneNodeInfo] = field(default_factory=list)

    def text(self) -> str:
        return "".join(self.preamble) + "".join("".join(s.lines) for s in self.sections)

    def node(self, path: str) -> SceneNodeInfo | None:
        return next((node for node in self.nodes if node.path == path), None)

    def resources(self, kind: str) -> dict[str, Section]:
        return {
            section.attr("id") or "": section for section in self.sections if section.kind == kind
        }

    def connections(self) -> list[Section]:
        return [section for section in self.sections if section.kind == "connection"]


def node_path(section: Section) -> str:
    parent = section.attr("parent")
    name = section.attr("name") or ""
    if parent is None:
        return "."
    return name if parent == "." else f"{parent}/{name}"


def parse_header(line: str) -> tuple[str, dict[str, str]] | None:
    match = _HEADER.match(line.strip())
    if match is None:
        return None
    return match.group(1), dict(_ATTRIBUTE.findall(match.group(2)))


def parse_scene(text: str) -> ParsedScene | None:
    """None for anything but a Godot 4 text scene."""
    preamble: list[str] = []
    sections: list[Section] = []
    for line in text.splitlines(keepends=True):
        header = parse_header(line) if line.startswith("[") else None
        if header is not None:
            sections.append(Section(header[0], header[1], [line]))
        elif sections:
            sections[-1].lines.append(line)
        else:
            preamble.append(line)
    if not sections or sections[0].kind != "gd_scene" or sections[0].attr("format") != "3":
        return None
    scene = ParsedScene(preamble, sections)
    external = scene.resources("ext_resource")
    for section in sections:
        if section.kind != "node":
            continue
        properties = section.properties()
        script_id = reference_id(properties.pop("script", ""))
        script = external[script_id].attr("path") if script_id in external else None
        instance_id = reference_id(section.attributes.get("instance", ""))
        instance = external[instance_id].attr("path") if instance_id in external else None
        scene.nodes.append(
            SceneNodeInfo(
                path=node_path(section),
                type=section.attr("type") or "",
                instance=instance,
                script=script,
                properties=properties,
                section=section,
            )
        )
    return scene


# Godot leaves out values that keep their default, so the AI reads a missing switch as "off".
# These go first, so the limit below never hides one of them.
SWITCHES = ("autostart", "one_shot", "visible", "disabled", "monitoring")
# Shapes, pictures and sounds are resources: as text they are useless, but the AI must know they
# are set, or it would think a hitbox has no shape and replace it.
RESOURCE_LABELS = {
    "shape": "(Form gesetzt)",
    "texture": "(Bild gesetzt)",
    "sprite_frames": "(Bilder gesetzt)",
    "stream": "(Ton gesetzt)",
}
_FIRST = (*SWITCHES, *RESOURCE_LABELS)


def short_properties(properties: dict[str, str], limit: int = 6) -> dict[str, str]:
    """A few simple values that help the AI; resources only say that they are set."""
    ordered = sorted(properties.items(), key=lambda item: item[0] not in _FIRST)
    picked: dict[str, str] = {}
    for name, value in ordered:
        if len(picked) >= limit:
            break
        if "Resource(" in value:
            if name in RESOURCE_LABELS:
                picked[name] = RESOURCE_LABELS[name]
            continue
        if len(value) > MAX_CONTEXT_VALUE or "\n" in value:
            continue
        picked[name] = value
    return picked
