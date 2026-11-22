"""What each exercise type emits."""

from __future__ import annotations

from exercise_helpers import _emitted, _next_focusable
from learnharness_protocol import (
    Choice,
    FindBugExercise,
    MultipleChoiceExercise,
    OrderingExercise,
    OrderItem,
    TextBlank,
    TextBlanksExercise,
)
from PyQt6.QtCore import Qt
from pytestqt.qtbot import QtBot

from learnharness_client.ui.exercises.find_bug import FindBugWidget
from learnharness_client.ui.exercises.multiple_choice import MultipleChoiceWidget
from learnharness_client.ui.exercises.ordering import OrderingWidget
from learnharness_client.ui.exercises.text_blanks import TextBlanksWidget


def test_text_blanks_emit_trimmed_answers(qtbot: QtBot) -> None:
    exercise = TextBlanksExercise(
        id="text",
        skill="s",
        difficulty=2,
        prompt="?",
        code="position.{{axis}} += {{value}} * delta",
        blanks=[TextBlank(id="axis"), TextBlank(id="value")],
    )
    widget = TextBlanksWidget(exercise)
    qtbot.addWidget(widget)
    assert _next_focusable(widget.inputs["axis"]) is widget.inputs["value"]
    widget.inputs["axis"].setText("  x ")
    widget.inputs["value"].setText("speed")
    assert _emitted(qtbot, widget).answers == {"axis": "x", "value": "speed"}


def test_multiple_choice_multi_select_emits_list(qtbot: QtBot) -> None:
    exercise = MultipleChoiceExercise(
        id="mc",
        skill="s",
        difficulty=1,
        prompt="Welche sind Zahlen?",
        multiple=True,
        choices=[Choice(id="a", text="1"), Choice(id="b", text="x"), Choice(id="c", text="2")],
    )
    widget = MultipleChoiceWidget(exercise)
    qtbot.addWidget(widget)
    widget.buttons["a"].setChecked(True)
    widget.buttons["c"].setChecked(True)
    assert _emitted(qtbot, widget).answers == {"choice": ["a", "c"]}


def test_multiple_choice_single_emits_choice(qtbot: QtBot) -> None:
    exercise = MultipleChoiceExercise(
        id="mc",
        skill="s",
        difficulty=1,
        prompt="?",
        code="position.x += 1",
        choices=[Choice(id="a", text="A"), Choice(id="b", text="B")],
    )
    widget = MultipleChoiceWidget(exercise)
    qtbot.addWidget(widget)
    widget.buttons["b"].setChecked(True)
    assert _emitted(qtbot, widget).answers == {"choice": "b"}


def test_ordering_keyboard_move_emits_new_order(qtbot: QtBot) -> None:
    exercise = OrderingExercise(
        id="ord",
        skill="s",
        difficulty=1,
        prompt="Sortiere.",
        items=[OrderItem(id="b", text="Zweitens"), OrderItem(id="a", text="Erstens")],
    )
    widget = OrderingWidget(exercise)
    qtbot.addWidget(widget)
    widget.items.setCurrentRow(1)
    qtbot.keyClick(widget.items, Qt.Key.Key_Up, Qt.KeyboardModifier.AltModifier)
    assert _emitted(qtbot, widget).answers == {"order": ["a", "b"]}


def test_find_bug_emits_selected_lines_and_explanation(qtbot: QtBot) -> None:
    exercise = FindBugExercise(
        id="bug",
        skill="s",
        difficulty=1,
        prompt="Wo ist der Fehler?",
        lines=["func _ready():", "\tprint(hallo)", "\tpass"],
    )
    widget = FindBugWidget(exercise)
    qtbot.addWidget(widget)
    widget.lines.item(1).setSelected(True)
    widget.explanation.setText("Anführungszeichen fehlen")
    submission = _emitted(qtbot, widget)
    assert submission.answers == {"lines": [2]}
    assert submission.explanation == "Anführungszeichen fehlen"


def test_find_bug_without_explanation_sends_none(qtbot: QtBot) -> None:
    exercise = FindBugExercise(
        id="bug", skill="s", difficulty=1, prompt="?", lines=["a", "b"], allow_multiple=True
    )
    widget = FindBugWidget(exercise)
    qtbot.addWidget(widget)
    widget.lines.item(0).setSelected(True)
    widget.lines.item(1).setSelected(True)
    submission = _emitted(qtbot, widget)
    assert submission.answers == {"lines": [1, 2]}
    assert submission.explanation is None
