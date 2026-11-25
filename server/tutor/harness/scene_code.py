"""What the code relies on: nodes of the scene, input actions and project files.

Exercises check only their new lines; a review checks the whole script and reports findings.
"""

from __future__ import annotations

import difflib
import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from learnharness_protocol import AddNode, RemoveNode, SceneChange, SceneContext

BUILT_IN_ACTIONS = frozenset(
    {"ui_left", "ui_right", "ui_up", "ui_down", "ui_accept", "ui_cancel", "ui_select"}
)
_NODE_REF = re.compile(r'\$"([^"]+)"|\$([A-Za-z_][\w/]*)|get_node\(\s*"([^"]+)"\s*\)')
_UNIQUE_REF = re.compile(r"(?<![\w)\]])%([A-Za-z_]\w*)")
_LOAD = re.compile(r'\b(?:pre)?load\(\s*"res://([^"]+)"\s*\)')
CHECKED_FILE_TYPES = (".tscn", ".gd")  # the client lists exactly these
MAX_LISTED_FILES = 200
MAX_FINDINGS = 8
_ACTION_USE = re.compile(
    r"\b(?:is_action(?:_just)?_(?:pressed|released)|get_action_strength|get_axis|get_vector)"
    r"\(([^)]*)\)"
)


def inside(path: str, node: str) -> bool:
    return node == "." or path == node or path.startswith(node + "/")


def _added_lines(before: str, after: str) -> list[str]:
    diff = difflib.ndiff(before.splitlines(), after.splitlines())
    return [line[2:] for line in diff if line.startswith("+ ")]


@dataclass
class _Known:
    """Everything a line of code may rely on."""

    actions: set[str]
    files: set[str] | None  # None: the list may be cut off, so nothing is checked
    scene: SceneContext | None
    paths: set[str] = field(default_factory=set)
    instances: set[str] = field(default_factory=set)

    @classmethod
    def build(
        cls,
        scene: SceneContext | None,
        actions: list[str],
        files: list[str] | None,
        changes: Sequence[SceneChange] = (),
    ) -> _Known:
        listed = (
            None
            if files is None or len(files) >= MAX_LISTED_FILES
            else {path.lstrip("/").casefold() for path in files}
        )
        known = cls(BUILT_IN_ACTIONS | set(actions), listed, scene)
        if scene is not None:
            known.paths = {node.path for node in scene.nodes}
            known.instances = {node.path for node in scene.nodes if node.instance}
            for change in changes:
                if isinstance(change, AddNode):
                    parent = "" if change.parent == "." else change.parent + "/"
                    known.paths.add(parent + change.name)
                elif isinstance(change, RemoveNode):
                    known.paths = {p for p in known.paths if not inside(p, change.node)}
        return known


def _action_problems(line: str, known: _Known) -> list[str]:
    return [
        f"Input-Aktion „{action}“ gibt es im Projekt nicht"
        for match in _ACTION_USE.finditer(line)
        for action in re.findall(r'"([^"]+)"', match.group(1))
        if action not in known.actions
    ]


def _node_problems(line: str, known: _Known) -> list[str]:
    scene = known.scene
    if scene is None:
        return []  # without a scene the nodes cannot be checked
    problems: list[str] = []
    base = "" if scene.script_node == "." else scene.script_node + "/"
    for match in _NODE_REF.finditer(line):
        reference = next(group for group in match.groups() if group)
        if reference.startswith(("/", "..", "%")) or ".." in reference.split("/"):
            continue  # outside the scene: not checked here
        parts = (base + reference).split("/")
        hidden = [p for i in range(1, len(parts)) if (p := "/".join(parts[:i])) in known.instances]
        if hidden:  # the nodes of an instanced scene are not in this file
            problems.append(f"Knoten in der Instanz {hidden[0]} sind nicht bekannt")
        elif base + reference not in known.paths:
            problems.append(f"Knoten {reference} gibt es in der Szene nicht")
    names = {path.rsplit("/", 1)[-1] for path in known.paths}
    problems += [
        f"Knoten %{match.group(1)} gibt es in der Szene nicht"
        for match in _UNIQUE_REF.finditer(line)
        if match.group(1) not in names
    ]
    return problems


def _file_problems(line: str, known: _Known) -> list[str]:
    if known.files is None:
        return []
    problems: list[str] = []
    for path in _LOAD.findall(line):
        folded = path.casefold()
        if folded.startswith("addons/") or not folded.endswith(CHECKED_FILE_TYPES):
            continue  # plug-ins and pictures or sounds are not listed
        if folded not in known.files:
            problems.append(f"Datei res://{path} gibt es im Projekt nicht")
    return problems


def _code(line: str) -> str:
    return line.split("#", 1)[0]


def check_code_uses_scene(
    scene: SceneContext | None,
    actions: list[str],
    changes: list[SceneChange],
    before: str,
    after: str,
) -> str | None:
    """New lines may only use nodes the scene will have and actions the project knows."""
    known = _Known.build(scene, actions, None, changes)
    added = [_code(line) for line in _added_lines(before, after)]
    for check in (_action_problems, _node_problems):
        for line in added:
            problems = check(line, known)
            if problems:
                return problems[0]
    return None


def check_loaded_files(files: list[str], before: str, after: str) -> str | None:
    """New preload()/load() calls may only name scenes and scripts the project has."""
    known = _Known.build(None, [], files)
    for line in _added_lines(before, after):
        problems = _file_problems(_code(line), known)
        if problems:
            return problems[0]
    return None


def _method_defined(code: str, method: str) -> bool:
    return re.search(rf"^\s*func\s+{re.escape(method)}\s*\(", code, re.MULTILINE) is not None


def scene_findings(
    scene: SceneContext | None,
    actions: list[str],
    files: list[str],
    code: str,
    start_line: int = 1,
) -> list[tuple[str, int | None]]:
    """Sure mistakes of a whole script, with their line (None for a mistake in the scene)."""
    known = _Known.build(scene, actions, files)
    found: list[tuple[str, int | None]] = []
    for number, line in enumerate(code.splitlines(), start=start_line):
        text = _code(line)
        for check in (_node_problems, _action_problems, _file_problems):
            found += [(problem, number) for problem in check(text, known)]
    if scene is not None:
        root = scene.root_name or "(Wurzel)"
        for link in scene.connections:
            if link.to_node == scene.script_node and not _method_defined(code, link.method):
                sender = root if link.from_node == "." else link.from_node
                found.append(
                    (f"Signal {sender}.{link.signal} führt zu {link.method}(), die fehlt", None)
                )
        for node in scene.nodes:
            name = node.path.rsplit("/", 1)[-1]
            started = re.search(rf"\b{re.escape(name)}\.start\(", code) is not None
            if node.type == "Timer" and node.properties.get("autostart") != "true" and not started:
                problem = f"Timer {node.path} startet in diesem Skript nicht, und autostart ist aus"
                found.append((problem, None))
    return found[:MAX_FINDINGS]
