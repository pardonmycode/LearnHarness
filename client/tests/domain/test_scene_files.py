"""Godot 4 scenes: read, found for a script and changed without touching anything else."""

from __future__ import annotations

from pathlib import Path

import pytest
from learnharness_protocol import (
    AddNode,
    ConnectSignal,
    DisconnectSignal,
    RemoveNode,
    SetProperty,
)

from learnharness_client.godot.scene_context import (
    find_scene,
    input_actions,
    project_files,
    read_scene,
    scene_context,
)
from learnharness_client.godot.scene_edit import SceneEditError, apply_scene_changes
from learnharness_client.godot.scene_file import parse_scene, short_properties

SCENE = """[gd_scene load_steps=3 format=3 uid="uid://abc"]

[ext_resource type="Script" uid="uid://s" path="res://player/player.gd" id="1_aa"]
[ext_resource type="PackedScene" path="res://ui/hud.tscn" id="2_bb"]

[node name="Player" type="CharacterBody2D"]
script = ExtResource("1_aa")
speed = 200

[node name="Sprite2D" type="Sprite2D" parent="."]
position = Vector2(4, 8)

[node name="Hud" parent="." instance=ExtResource("2_bb")]

[node name="Area" type="Area2D" parent="."]

[node name="Shape" type="CollisionShape2D" parent="Area"]

[connection signal="body_entered" from="Area" to="." method="_on_area_body_entered"]
"""


def test_scene_is_read_as_a_node_tree() -> None:
    scene = parse_scene(SCENE)
    assert scene is not None and scene.text() == SCENE
    assert [node.path for node in scene.nodes] == [".", "Sprite2D", "Hud", "Area", "Area/Shape"]
    root = scene.node(".")
    assert root is not None and root.script == "res://player/player.gd"
    assert root.properties == {"speed": "200"}
    hud = scene.node("Hud")
    assert hud is not None and hud.instance == "res://ui/hud.tscn" and hud.type == ""


def test_godot_3_scenes_are_left_alone() -> None:
    assert parse_scene('[gd_scene load_steps=2 format=2]\n\n[node name="A" type="Node"]\n') is None


def test_new_nodes_values_and_signals_land_in_the_right_place() -> None:
    changes = [
        AddNode(parent="Area", name="Hitbox", type="CollisionShape2D"),
        SetProperty(node="Area/Hitbox", property="shape", value="CircleShape2D(radius=16)"),
        SetProperty(node="Sprite2D", property="position", value="Vector2(1, 2)"),
        AddNode(parent=".", name="Timer", type="Timer"),
        ConnectSignal(signal="timeout", from_node="Timer", to_node=".", method="_on_timeout"),
    ]
    new = apply_scene_changes(SCENE, changes)
    scene = parse_scene(new)
    assert scene is not None
    assert [node.path for node in scene.nodes][-3:] == ["Area/Shape", "Area/Hitbox", "Timer"]
    assert "position = Vector2(1, 2)" in new and "Vector2(4, 8)" not in new
    assert new.startswith("[gd_scene load_steps=4 format=3")
    shapes = scene.resources("sub_resource")
    assert len(shapes) == 1 and "radius = 16" in "".join(next(iter(shapes.values())).lines)
    hitbox = scene.node("Area/Hitbox")
    assert hitbox is not None and hitbox.properties["shape"].startswith('SubResource("Circle')
    assert new.endswith('[connection signal="timeout" from="Timer" to="." method="_on_timeout"]\n')
    # everything else is exactly as before
    assert '[node name="Hud" parent="." instance=ExtResource("2_bb")]' in new


def test_removing_a_node_takes_its_children_and_signals() -> None:
    new = apply_scene_changes(SCENE, [RemoveNode(node="Area")])
    assert "Area" not in new and "body_entered" not in new and "Sprite2D" in new


def test_disconnecting_removes_only_that_signal() -> None:
    change = DisconnectSignal(
        signal="body_entered", from_node="Area", to_node=".", method="_on_area_body_entered"
    )
    new = apply_scene_changes(SCENE, [change])
    assert "[connection" not in new and '[node name="Area"' in new


@pytest.mark.parametrize(
    "change",
    [
        AddNode(parent="Missing", name="X", type="Timer"),
        AddNode(parent=".", name="Sprite2D", type="Sprite2D"),
        SetProperty(node="Missing", property="visible", value="false"),
        RemoveNode(node="."),
        ConnectSignal(signal="timeout", from_node="Missing", to_node=".", method="_x"),
        DisconnectSignal(signal="pressed", from_node="Area", to_node=".", method="_x"),
    ],
)
def test_changes_that_do_not_fit_change_nothing(change: object) -> None:
    with pytest.raises(SceneEditError):
        apply_scene_changes(SCENE, [change])  # type: ignore[list-item]


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "game"
    (root / "player").mkdir(parents=True)
    (root / "project.godot").write_text(
        'config_version=5\n\n[input]\n\nspringen={\n"deadzone": 0.5,\n"events": []\n}\n'
        'schiessen={\n"deadzone": 0.5,\n"events": []\n}\n\n[rendering]\nx=1\n',
        encoding="utf-8",
    )
    (root / "player" / "player.tscn").write_text(SCENE, encoding="utf-8")
    (root / "player" / "player.gd").write_text("extends CharacterBody2D\n", encoding="utf-8")
    return root


def test_scene_of_a_script_is_found_and_described(tmp_path: Path) -> None:
    root = _project(tmp_path)
    found = find_scene(root, "player/player.gd")
    assert found is not None and found.relative == "player/player.tscn"
    assert found.script_node == "."
    context = scene_context(found)
    assert context is not None and context.path == "player/player.tscn"
    assert context.root_name == "Player"
    assert context.nodes[1].properties == {"position": "Vector2(4, 8)"}
    assert context.connections[0].method == "_on_area_body_entered"
    assert find_scene(root, "other.gd") is None
    assert read_scene(root, "../outside.tscn") is None


def test_input_actions_come_from_the_input_map(tmp_path: Path) -> None:
    assert input_actions(_project(tmp_path)) == ["springen", "schiessen"]
    assert input_actions(tmp_path) == []


def test_project_files_list_scenes_first(tmp_path: Path) -> None:
    root = _project(tmp_path)
    (root / "main.gd").write_text("extends Node\n", encoding="utf-8")
    assert project_files(root) == ["player/player.tscn", "main.gd", "player/player.gd"]


def test_switches_are_never_cut_off() -> None:
    values = {f"value_{i}": str(i) for i in range(8)} | {"one_shot": "true", "autostart": "true"}
    picked = short_properties(values)
    assert len(picked) == 6 and picked["autostart"] == "true" and picked["one_shot"] == "true"


def test_resources_only_say_that_they_are_set() -> None:
    values = {
        "shape": 'SubResource("CircleShape2D_ab")',
        "texture": 'ExtResource("2_cd")',
        "material": 'SubResource("Mat_1")',
        "position": "Vector2(1, 2)",
    }
    assert short_properties(values) == {
        "shape": "(Form gesetzt)",
        "texture": "(Bild gesetzt)",
        "position": "Vector2(1, 2)",
    }
