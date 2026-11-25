"""Scene changes from the AI: parsed strictly and played through on the node list."""

from __future__ import annotations

from typing import Any

import pytest
from learnharness_protocol import SceneConnection, SceneContext, SceneNode

from tutor.harness import HarnessRejected
from tutor.harness.scene_check import (
    check_code_uses_scene,
    check_loaded_files,
    check_scene_changes,
    parse_scene_changes,
)

SCENE = SceneContext(
    path="player/player.tscn",
    script_node=".",
    nodes=[
        SceneNode(path=".", type="CharacterBody2D", script="res://player/player.gd"),
        SceneNode(path="Sprite2D", type="Sprite2D"),
        SceneNode(path="Hud", instance="res://ui/hud.tscn"),
    ],
    connections=[
        SceneConnection(signal="ready", from_node="Sprite2D", to_node=".", method="_on_ready")
    ],
)
BEFORE = "extends CharacterBody2D\n\nvar speed = 200\n"


def flat(op: str, **fields: str) -> dict[str, str]:
    keys = ("parent", "name", "type", "node", "property", "value", "signal", "from", "to")
    return {"op": op, **dict.fromkeys(keys, ""), "method": "", **fields}


def test_flat_ai_entries_become_protocol_changes() -> None:
    changes = parse_scene_changes(
        [
            flat("add_node", parent=".", name="Timer", type="Timer"),
            flat("set_property", node="Timer", property="wait_time", value="2.0"),
            flat("connect", signal="timeout", **{"from": "Timer", "to": "."}, method="_tick"),
        ]
    )
    assert [change.op for change in changes] == ["add_node", "set_property", "connect"]


@pytest.mark.parametrize(
    "item",
    [
        flat("delete_everything"),
        flat("add_node", parent=".", name="X", type="EditorPlugin"),
        flat("add_node", parent=".", name="Böse Name", type="Timer"),
        flat("set_property", node="Sprite2D", property="script", value='"x"'),
        flat("set_property", node="Sprite2D", property="texture", value='ExtResource("1")'),
        flat("set_property", node="../Other", property="visible", value="true"),
    ],
)
def test_unsafe_entries_are_rejected(item: dict[str, Any]) -> None:
    with pytest.raises(HarnessRejected):
        parse_scene_changes([item])


def test_too_many_changes_are_rejected() -> None:
    with pytest.raises(HarnessRejected):
        parse_scene_changes([flat("remove_node", node="Sprite2D")] * 9)


def _check(items: list[dict[str, str]], code: str = BEFORE) -> str | None:
    return check_scene_changes(SCENE, parse_scene_changes(items), code)


def test_changes_are_played_through_in_order() -> None:
    code = BEFORE + "\nfunc _tick():\n\tpass\n"
    assert (
        _check(
            [
                flat("add_node", parent=".", name="Timer", type="Timer"),
                flat("set_property", node="Timer", property="autostart", value="true"),
                flat("connect", signal="timeout", **{"from": "Timer", "to": "."}, method="_tick"),
            ],
            code,
        )
        is None
    )


@pytest.mark.parametrize(
    ("items", "reason"),
    [
        ([flat("set_property", node="Timer", property="visible", value="true")], "Timer"),
        ([flat("add_node", parent=".", name="Sprite2D", type="Sprite2D")], "schon"),
        ([flat("remove_node", node=".")], "nicht entfernt"),
        (
            [
                flat("add_node", parent=".", name="Timer", type="Timer"),
                flat("connect", signal="pressed", **{"from": "Timer", "to": "."}, method="_x"),
            ],
            "kein Signal",
        ),
        (
            [
                flat("add_node", parent=".", name="Timer", type="Timer"),
                flat("connect", signal="timeout", **{"from": "Timer", "to": "."}, method="_x"),
            ],
            "func _x()",
        ),
        (
            [flat("disconnect", signal="x", **{"from": "Sprite2D", "to": "."}, method="_y")],
            "gibt es nicht",
        ),
    ],
)
def test_changes_that_do_not_fit_the_scene_are_named(
    items: list[dict[str, str]], reason: str
) -> None:
    problem = _check(items)
    assert problem is not None and reason in problem


def test_removing_a_node_also_drops_its_signals() -> None:
    items = [
        flat("remove_node", node="Sprite2D"),
        flat("disconnect", signal="ready", **{"from": "Sprite2D", "to": "."}, method="_on_ready"),
    ]
    assert "gibt es nicht" in (_check(items) or "")


def test_new_code_may_only_use_nodes_the_scene_will_have() -> None:
    after = BEFORE + "\nfunc _ready():\n\t$Timer.start()\n"
    assert "Timer" in (check_code_uses_scene(SCENE, [], [], BEFORE, after) or "")
    added = parse_scene_changes([flat("add_node", parent=".", name="Timer", type="Timer")])
    assert check_code_uses_scene(SCENE, [], added, BEFORE, after) is None


def test_node_checks_skip_comments_modulo_and_outside_paths() -> None:
    after = BEFORE + (
        "\nfunc _ready():\n\t$Hud.visible = false  # $Missing in a comment\n"
        '\tvar rest = speed % 7\n\t$Sprite2D.visible = true\n\tget_node("../Level")\n'
    )
    assert check_code_uses_scene(SCENE, [], [], BEFORE, after) is None


def test_nodes_inside_an_instance_are_unknown() -> None:
    after = BEFORE + "\nfunc _ready():\n\t$Hud/Score.text = 'x'\n"
    assert "Instanz Hud" in (check_code_uses_scene(SCENE, [], [], BEFORE, after) or "")
    items = [flat("add_node", parent="Hud", name="Extra", type="Label")]
    assert "Instanz Hud" in (_check(items) or "")


def test_only_existing_scenes_and_scripts_are_loaded() -> None:
    after = BEFORE + '\nvar slime = preload("res://entities/enemies/slime/slime.tscn")\n'
    assert "slime.tscn" in (check_loaded_files(["player/player.tscn"], BEFORE, after) or "")
    files = ["player/player.tscn", "entities/enemies/slime/slime.tscn"]
    assert check_loaded_files(files, BEFORE, after) is None
    sound = BEFORE + '\nvar boing = load("res://assets/audio/boing.wav")\n'
    assert check_loaded_files([], BEFORE, sound) is None
    assert check_loaded_files([f"x{i}.gd" for i in range(200)], BEFORE, after) is None


def test_only_known_input_actions_are_allowed() -> None:
    after = BEFORE + '\nfunc _process(_d):\n\tif Input.is_action_pressed("springen"):\n\t\tpass\n'
    assert "springen" in (check_code_uses_scene(SCENE, [], [], BEFORE, after) or "")
    assert check_code_uses_scene(SCENE, ["springen"], [], BEFORE, after) is None
    built_in = after.replace("springen", "ui_accept")
    assert check_code_uses_scene(None, [], [], BEFORE, built_in) is None


def test_without_a_scene_only_actions_are_checked() -> None:
    after = BEFORE + "\nfunc _ready():\n\t$Anything.show()\n"
    assert check_code_uses_scene(None, [], [], BEFORE, after) is None


def test_new_timers_must_start_and_new_shapes_need_a_form() -> None:
    timer = [flat("add_node", parent=".", name="Timer", type="Timer")]
    assert "startet nie" in (_check(timer) or "")
    started = BEFORE + "\nfunc _ready():\n\t$Timer.start()\n"
    assert _check(timer, started) is None
    shape = [
        flat("add_node", parent=".", name="Hitbox", type="Area2D"),
        flat("add_node", parent="Hitbox", name="Form", type="CollisionShape2D"),
    ]
    assert "keine Form" in (_check(shape) or "")
    with_form = flat(
        "set_property", node="Hitbox/Form", property="shape", value="CircleShape2D(radius=16)"
    )
    assert _check([*shape, with_form]) is None


def test_an_existing_shape_is_never_replaced() -> None:
    scene = SCENE.model_copy(deep=True)
    scene.nodes.append(
        SceneNode(path="Hitbox", type="CollisionShape2D", properties={"shape": "(Form gesetzt)"})
    )
    items = [flat("set_property", node="Hitbox", property="shape", value="CircleShape2D(radius=8)")]
    problem = check_scene_changes(scene, parse_scene_changes(items), BEFORE)
    assert problem is not None and "schon eine Form" in problem
