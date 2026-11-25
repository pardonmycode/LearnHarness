"""Finds the scene of the open script and the input actions of the project."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from learnharness_protocol import SceneConnection, SceneContext, SceneNode
from pydantic import ValidationError

from ..domain.path_guard import PathGuard, PathNotAllowed
from .scene_file import MAX_SCENE_BYTES, ParsedScene, parse_scene, short_properties

MAX_SCENES_SCANNED = 400
MAX_CONTEXT_NODES = 150
MAX_CONTEXT_CONNECTIONS = 80
MAX_PROJECT_FILES = 200
_ACTION = re.compile(r"^([A-Za-z_][\w.\-]*)\s*=\s*\{", re.MULTILINE)


@dataclass
class FoundScene:
    path: Path  # absolute
    relative: str  # posix, relative to the project
    text: str
    scene: ParsedScene
    script_node: str


def _read(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_SCENE_BYTES:
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def scene_guard(root: Path) -> PathGuard:
    return PathGuard(root, allowed_suffixes=frozenset({".tscn"}))


def read_scene(root: Path, relative: str) -> FoundScene | None:
    """One scene by its project path, checked like every other file access."""
    try:
        path = scene_guard(root).ensure_allowed(relative)
    except PathNotAllowed:
        return None
    text = _read(path)
    scene = parse_scene(text) if text is not None else None
    if text is None or scene is None:
        return None
    return FoundScene(path, relative, text, scene, ".")


def find_scene(root: Path, script_relative: str) -> FoundScene | None:
    """The scene whose node uses this script; a scene where it is the root comes first."""
    try:
        guard = scene_guard(root)
    except PathNotAllowed:
        return None
    wanted = "res://" + script_relative.replace("\\", "/").lstrip("/")
    best: FoundScene | None = None
    for path in guard.iter_scripts()[:MAX_SCENES_SCANNED]:
        text = _read(path)
        if text is None or wanted not in text:
            continue
        scene = parse_scene(text)
        if scene is None:
            continue
        node = next((item for item in scene.nodes if item.script == wanted), None)
        if node is None:
            continue
        relative = path.relative_to(guard.root).as_posix()
        found = FoundScene(path, relative, text, scene, node.path)
        if node.path == ".":
            return found
        best = best or found
    return best


def scene_context(found: FoundScene) -> SceneContext | None:
    """What the AI may know of the scene: names, types, a few values and the signals."""
    nodes = [
        SceneNode(
            path=node.path,
            type=node.type,
            instance=node.instance,
            script=node.script,
            properties=short_properties(node.properties),
        )
        for node in found.scene.nodes[:MAX_CONTEXT_NODES]
    ]
    connections = [
        SceneConnection(
            signal=section.attr("signal") or "",
            from_node=section.attr("from") or "",
            to_node=section.attr("to") or "",
            method=section.attr("method") or "",
        )
        for section in found.scene.connections()[:MAX_CONTEXT_CONNECTIONS]
    ]
    try:
        root = found.scene.node(".")
        return SceneContext(
            path=found.relative,
            root_name=((root.section.attr("name") or "") if root else "")[:80],
            script_node=found.script_node,
            nodes=nodes,
            connections=connections,
        )
    except ValidationError:
        return None  # e.g. node names Godot allows but the protocol does not


def input_actions(root: Path) -> list[str]:
    """Action names of the [input] section in project.godot (the Godot input map)."""
    try:
        text = (root / "project.godot").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    section = re.search(r"^\[input\]\s*$(.*?)(?=^\[|\Z)", text, re.MULTILINE | re.DOTALL)
    if section is None:
        return []
    names = dict.fromkeys(name[:64] for name in _ACTION.findall(section.group(1)))
    return list(names)[:64]


def project_files(root: Path) -> list[str]:
    """Scenes and scripts of the project, so new code only loads files that exist."""
    try:
        guard = PathGuard(root, allowed_suffixes=frozenset({".tscn", ".gd"}))
    except PathNotAllowed:
        return []
    files = [path.relative_to(guard.root).as_posix() for path in guard.iter_scripts()]
    scenes = [path for path in files if path.endswith(".tscn")]
    scripts = [path for path in files if not path.endswith(".tscn")]
    return [*scenes, *scripts][:MAX_PROJECT_FILES]  # scenes matter most for preload()
