"""Godot scenes: what the AI may see of a .tscn file and the changes it may make.

Changes are small, checked steps instead of a whole new file: a scene file holds ids and
resources the AI must never break. Client and server both use the checks below.
"""

from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import Field, ValidationInfo, field_validator

from .base import ProtocolModel

MAX_SCENE_CHANGES = 8
# Nodes a child's game typically needs; anything else is added in Godot by hand.
NODE_TYPES = frozenset(
    {
        "Node", "Node2D", "Node3D", "Control", "CanvasLayer", "Timer",
        "Sprite2D", "AnimatedSprite2D", "AnimationPlayer", "Camera2D", "Marker2D",
        "CharacterBody2D", "RigidBody2D", "StaticBody2D", "Area2D", "CollisionShape2D",
        "RayCast2D", "Line2D", "Polygon2D", "PointLight2D", "CPUParticles2D",
        "GPUParticles2D", "Path2D", "PathFollow2D", "NavigationAgent2D", "TileMapLayer",
        "VisibleOnScreenNotifier2D", "AudioStreamPlayer", "AudioStreamPlayer2D",
        "Label", "Button", "LineEdit", "CheckBox", "TextureRect", "ColorRect", "Panel",
        "ProgressBar", "HBoxContainer", "VBoxContainer", "MarginContainer",
        "CenterContainer", "MeshInstance3D", "Camera3D", "CharacterBody3D",
        "StaticBody3D", "Area3D", "CollisionShape3D", "DirectionalLight3D",
    }
)  # fmt: skip
NEW_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,39}$")
# Existing nodes may have spaces or umlauts; quotes, brackets and % would break the file.
_SEGMENT = r'[^"\\\[\]\n:%@/.][^"\\\[\]\n:%@/]{0,79}'
NODE_PATH = re.compile(rf"^(?:\.|{_SEGMENT}(?:/{_SEGMENT})*)$")
PROPERTY = re.compile(r"^[a-z_][a-z0-9_]*(?:/[a-z0-9_]+)*$")
IDENTIFIER = re.compile(r"^[a-z_][A-Za-z0-9_]{0,63}$")
FORBIDDEN_PROPERTIES = frozenset({"script"})

_NUM = r"-?\d+(?:\.\d+)?(?:e-?\d+)?"
_S = r"\ ?"  # VERBOSE patterns ignore plain spaces
_VALUE = re.compile(
    rf"""^(?:{_NUM}|true|false|"(?:[^"\\\n]|\\["\\nt])*"
    |Vector2i?\({_NUM},{_S}{_NUM}\)|Vector3i?\({_NUM},{_S}{_NUM},{_S}{_NUM}\)
    |Color\({_NUM},{_S}{_NUM},{_S}{_NUM}(?:,{_S}{_NUM})?\))$""",
    re.VERBOSE,
)
# Only for "shape": the client turns this into a [sub_resource] of the scene.
SHAPE_VALUE = re.compile(
    rf"""^(?:RectangleShape2D\(size=Vector2\({_NUM},{_S}{_NUM}\)\)
    |CircleShape2D\(radius={_NUM}\)
    |CapsuleShape2D\(radius={_NUM},{_S}height={_NUM}\)
    |BoxShape3D\(size=Vector3\({_NUM},{_S}{_NUM},{_S}{_NUM}\)\)
    |SphereShape3D\(radius={_NUM}\))$""",
    re.VERBOSE,
)
MAX_VALUE_LENGTH = 200


def value_problem(property_name: str, value: str) -> str | None:
    """Why this property value may not go into a scene, or None if it may."""
    if not PROPERTY.match(property_name) or property_name in FORBIDDEN_PROPERTIES:
        return f"Eigenschaft „{property_name}“ ist nicht erlaubt"
    if len(value) > MAX_VALUE_LENGTH:
        return "Wert zu lang"
    if property_name == "shape":
        return (
            None
            if SHAPE_VALUE.match(value)
            else "Form muss z. B. CircleShape2D(radius=16) sein"
        )
    return (
        None if _VALUE.match(value) else f"Wert „{value}“ ist kein einfacher Godot-Wert"
    )


NodePath = Annotated[
    str, Field(min_length=1, max_length=300, pattern=NODE_PATH.pattern)
]
Identifier = Annotated[
    str, Field(min_length=1, max_length=64, pattern=IDENTIFIER.pattern)
]


class SceneNode(ProtocolModel):
    path: NodePath  # "." is the root, "UI/Label" a grandchild
    type: str = Field(default="", max_length=64)  # empty for an instanced scene
    instance: str | None = Field(default=None, max_length=300)  # res:// path
    script: str | None = Field(default=None, max_length=300)
    properties: dict[str, str] = Field(default_factory=dict, max_length=8)


class SceneConnection(ProtocolModel):
    signal: str = Field(min_length=1, max_length=64)
    from_node: str = Field(min_length=1, max_length=300)
    to_node: str = Field(min_length=1, max_length=300)
    method: str = Field(min_length=1, max_length=64)


class SceneContext(ProtocolModel):
    """The scene the open script belongs to, as far as the AI needs it."""

    path: str = Field(min_length=6, max_length=500)  # relative to the project
    root_name: str = Field(
        default="", max_length=80
    )  # as Godot shows it, e.g. "Player"
    script_node: NodePath  # the node the open script is attached to
    nodes: list[SceneNode] = Field(min_length=1, max_length=150)
    connections: list[SceneConnection] = Field(default_factory=list, max_length=80)


class AddNode(ProtocolModel):
    op: Literal["add_node"] = "add_node"
    parent: NodePath
    name: str = Field(pattern=NEW_NAME.pattern)
    type: str

    @field_validator("type")
    @classmethod
    def known_type(cls, value: str) -> str:
        if value not in NODE_TYPES:
            raise ValueError(f"Knotentyp {value} ist nicht erlaubt")
        return value


class SetProperty(ProtocolModel):
    op: Literal["set_property"] = "set_property"
    node: NodePath
    property: str = Field(max_length=64)
    value: str = Field(max_length=MAX_VALUE_LENGTH)

    @field_validator("value")
    @classmethod
    def simple_value(cls, value: str, info: ValidationInfo) -> str:
        name = str(info.data.get("property", ""))
        problem = value_problem(name, value)
        if problem:
            raise ValueError(problem)
        return value


class RemoveNode(ProtocolModel):
    op: Literal["remove_node"] = "remove_node"
    node: NodePath


class ConnectSignal(ProtocolModel):
    op: Literal["connect"] = "connect"
    signal: Identifier
    from_node: NodePath
    to_node: NodePath
    method: Identifier


class DisconnectSignal(ProtocolModel):
    op: Literal["disconnect"] = "disconnect"
    signal: Identifier
    from_node: NodePath
    to_node: NodePath
    method: Identifier


SceneChange = Annotated[
    AddNode | SetProperty | RemoveNode | ConnectSignal | DisconnectSignal,
    Field(discriminator="op"),
]


class SceneEdit(ProtocolModel):
    """Changes to one scene file; the client applies them in this order."""

    path: str = Field(min_length=6, max_length=500)
    changes: list[SceneChange] = Field(min_length=1, max_length=MAX_SCENE_CHANGES)
    explanation: str = Field(default="", max_length=1000)

    @field_validator("path")
    @classmethod
    def scene_file(cls, value: str) -> str:
        if not value.casefold().endswith(".tscn"):
            raise ValueError("Nur .tscn-Szenen können geändert werden")
        return value
