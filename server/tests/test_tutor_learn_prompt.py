"""The LearnAgent prompt has no contradicting rules."""

from __future__ import annotations

from typing import Any

import pytest

from tutor import harness
from tutor.models import AiSettings


def _two_blanks(kind: str) -> dict[str, Any]:
    blanks: list[dict[str, Any]] = (
        [{"options": ["a", "b"], "answer": "a"}, {"options": ["c", "d"], "answer": "c"}]
        if kind == "fill_blanks"
        else [{"answer": "a", "alternatives": []}, {"answer": "c", "alternatives": []}]
    )
    return {
        "message": "Los",
        "skill": "loops",
        "kind": kind,
        "prompt": "Was fehlt?",
        "code": "{{1}} += {{2}}",
        "choices": [],
        "blanks": blanks,
        "explanation_after_correct": "Gut",
        "new_file_content": "",
    }


@pytest.mark.django_db
def test_code_fields_are_exempt_from_the_chat_rules() -> None:
    system = harness.system_prompt("learn", AiSettings.load(), learning_level=5)
    for field in ("code", "ordered_lines", "buggy_lines", "new_file_content"):
        assert f'"{field}"' in system[: system.index("3. Führe")]


@pytest.mark.parametrize(("level", "kind"), [(3, "fill_blanks"), (6, "text_blanks")])
def test_single_blank_levels(level: int, kind: str) -> None:
    text = harness.level_instructions(level)
    assert "genau einer Lücke" in text and "1 bis 2" not in text and "{each}" not in text
    with pytest.raises(harness.HarnessRejected, match="genau eine Lücke"):
        harness.build_exercise(_two_blanks(kind), max_lines=3, prefix="learn", level=level)


@pytest.mark.parametrize(("level", "kind"), [(4, "fill_blanks"), (7, "text_blanks")])
def test_two_blanks_stay_allowed_on_the_next_level(level: int, kind: str) -> None:
    assert "1 bis 2 Lücken" in harness.level_instructions(level)
    built = harness.build_exercise(_two_blanks(kind), max_lines=3, prefix="learn", level=level)
    assert len(built.exercise.blanks) == 2


def test_focus_is_allowed_without_claiming_the_child_knows_it() -> None:
    note = harness.learn_topics_note({"variables": 2}, True)
    assert "kennt das Kind schon: variables." in note
    assert "nur diese und den Übungsschwerpunkt" in note
    assert "den Übungsschwerpunkt" not in harness.learn_topics_note({"variables": 2})
    empty = harness.learn_topics_note({}, True)
    assert (
        "einfachsten Anweisungen und den Übungsschwerpunkt" in empty
        and "kennt das Kind" not in empty
    )
