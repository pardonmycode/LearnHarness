"""Scene changes: only simple, checked values and known node types."""

from __future__ import annotations

import pytest
from learnharness_protocol import AddNode, ReviewResult, SceneEdit, SetProperty
from learnharness_protocol.scenes import value_problem
from pydantic import ValidationError


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("wait_time", "2.0"),
        ("visible", "false"),
        ("text", '"Hallo Welt"'),
        ("text", '"Sag \\"Hi\\""'),
        ("position", "Vector2(10, -20.5)"),
        ("position", "Vector2(10,20)"),
        ("modulate", "Color(1, 0, 0, 1)"),
        ("shape", "RectangleShape2D(size=Vector2(32, 32))"),
        ("shape", "CapsuleShape2D(radius=8, height=30)"),
        ("theme_override_font_sizes/font_size", "24"),
    ],
)
def test_simple_godot_values_are_allowed(name: str, value: str) -> None:
    assert value_problem(name, value) is None


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("script", '"res://x.gd"'),
        ("texture", 'ExtResource("1_ab")'),
        ("text", '"zwei\nZeilen"'),
        ("text", '"offen'),
        ("position", 'Vector2(1, 2)]\n[node name="X"]'),
        ("shape", "Vector2(1, 2)"),
        ("Position", "1"),
        ("text", '"' + "x" * 300 + '"'),
    ],
)
def test_anything_else_is_rejected(name: str, value: str) -> None:
    assert value_problem(name, value) is not None


def test_only_known_node_types_and_safe_names() -> None:
    assert AddNode(parent=".", name="Timer_2", type="Timer").type == "Timer"
    for bad in (
        {"parent": ".", "name": "X", "type": "EditorScript"},
        {"parent": ".", "name": "a b", "type": "Timer"},
        {"parent": "../Level", "name": "X", "type": "Timer"},
        {"parent": 'A"]', "name": "X", "type": "Timer"},
    ):
        with pytest.raises(ValidationError):
            AddNode(**bad)


def test_scene_edits_need_a_correct_answer_and_a_scene_file() -> None:
    edit = SceneEdit(
        path="main.tscn",
        changes=[SetProperty(node=".", property="visible", value="true")],
    )
    with pytest.raises(ValidationError):
        ReviewResult(correct=False, feedback="nein", scene_edits=[edit])
    assert ReviewResult(correct=True, feedback="ja", scene_edits=[edit]).scene_edits
    with pytest.raises(ValidationError):
        SceneEdit(path="player.gd", changes=edit.changes)
