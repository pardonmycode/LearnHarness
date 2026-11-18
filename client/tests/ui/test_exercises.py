from __future__ import annotations

from learnharness_protocol import (
    Blank,
    Choice,
    FillBlanksExercise,
    FindBugExercise,
    MultipleChoiceExercise,
    OrderingExercise,
    OrderItem,
    ReviewResult,
    Submission,
    TextBlank,
    TextBlanksExercise,
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QWidget
from pytestqt.qtbot import QtBot

from learnharness_client.ui.exercises.base import ExerciseWidget
from learnharness_client.ui.exercises.factory import create_exercise_widget
from learnharness_client.ui.exercises.fill_blanks import FillBlanksWidget
from learnharness_client.ui.exercises.find_bug import FindBugWidget
from learnharness_client.ui.exercises.multiple_choice import MultipleChoiceWidget
from learnharness_client.ui.exercises.ordering import OrderingWidget
from learnharness_client.ui.exercises.text_blanks import TextBlanksWidget


def test_fill_blank_submission(qtbot: QtBot) -> None:
    exercise = FillBlanksExercise(
        id="fill",
        skill="Koordinaten",
        difficulty=1,
        prompt="Ergänze.",
        code="position.{{blank_1}} += 10",
        blanks=[Blank(id="blank_1", options=["x", "y"])],
    )
    widget = FillBlanksWidget(exercise)
    qtbot.addWidget(widget)
    widget.inputs["blank_1"].setCurrentIndex(1)
    submission = widget.answers()
    assert submission.answers == {"blank_1": "x"}
    widget.show_result(ReviewResult(correct=True, feedback="Gut!"))
    assert "✓" in widget.result_label.text()


def test_multiple_choice_submission(qtbot: QtBot) -> None:
    exercise = MultipleChoiceExercise(
        id="choice",
        skill="Koordinaten",
        difficulty=1,
        prompt="Welche Achse?",
        choices=[Choice(id="x", text="X"), Choice(id="y", text="Y")],
    )
    widget = MultipleChoiceWidget(exercise)
    qtbot.addWidget(widget)
    widget.buttons["x"].setChecked(True)
    assert widget.answers().answers == {"choice": "x"}


def test_free_text_blanks_submission(qtbot: QtBot) -> None:
    exercise = TextBlanksExercise(
        id="text",
        skill="Koordinaten",
        difficulty=2,
        prompt="Ergänze ohne Auswahl.",
        code="position.{{axis}} += {{value}} * delta",
        blanks=[TextBlank(id="axis"), TextBlank(id="value")],
    )
    widget = TextBlanksWidget(exercise)
    qtbot.addWidget(widget)
    widget.inputs["axis"].setText("x")
    widget.inputs["value"].setText("speed")
    assert widget.answers().answers == {"axis": "x", "value": "speed"}


# --- Every exercise type: input -> emitted Submission -------------------------


def _next_focusable(widget: QWidget) -> QWidget:
    """The widget Tab moves to (labels inside the code are skipped)."""
    current = widget.nextInFocusChain()
    while current.focusPolicy() == Qt.FocusPolicy.NoFocus:
        current = current.nextInFocusChain()
    return current


def _emitted(qtbot: QtBot, widget: ExerciseWidget) -> Submission:
    with qtbot.waitSignal(widget.submitted, timeout=1000) as signal:
        widget.submit_button.click()
    submission = signal.args[0]
    assert isinstance(submission, Submission)
    return submission


def _fill() -> FillBlanksExercise:
    return FillBlanksExercise(
        id="fill",
        skill="Bewegung",
        difficulty=1,
        prompt="Ergänze.",
        code="func _process(delta):\n\tposition.{{axis}} += {{speed}} * delta",
        blanks=[Blank(id="speed", options=["speed", "10"]), Blank(id="axis", options=["x", "y"])],
    )


def test_factory_creates_a_widget_for_every_type(qtbot: QtBot) -> None:
    exercises = [
        _fill(),
        MultipleChoiceExercise(
            id="mc",
            skill="s",
            difficulty=1,
            prompt="?",
            choices=[Choice(id="a", text="A"), Choice(id="b", text="B")],
        ),
        OrderingExercise(
            id="ord",
            skill="s",
            difficulty=1,
            prompt="?",
            items=[OrderItem(id="a", text="A"), OrderItem(id="b", text="B")],
        ),
        FindBugExercise(id="bug", skill="s", difficulty=1, prompt="?", lines=["a", "b"]),
        TextBlanksExercise(
            id="tb", skill="s", difficulty=1, prompt="?", code="{{a}}", blanks=[TextBlank(id="a")]
        ),
    ]
    for exercise in exercises:
        widget = create_exercise_widget(exercise)
        qtbot.addWidget(widget)
        assert isinstance(widget, ExerciseWidget), exercise.kind


def test_fill_blanks_are_embedded_inline_in_reading_order(qtbot: QtBot) -> None:
    widget = FillBlanksWidget(_fill())
    qtbot.addWidget(widget)
    # Numbering follows the code, not the order of the blank list.
    assert list(widget.inputs) == ["axis", "speed"]
    assert widget.inputs["axis"].accessibleName() == "Lücke 1"
    assert widget.inputs["speed"].accessibleName() == "Lücke 2"
    code_frame = widget.findChild(QFrame, "inlineCode")
    assert code_frame is not None
    assert code_frame.isAncestorOf(widget.inputs["axis"])
    assert code_frame.isAncestorOf(widget.inputs["speed"])
    assert _next_focusable(widget.inputs["axis"]) is widget.inputs["speed"]
    assert _next_focusable(widget.inputs["speed"]) is widget.submit_button
    widget.inputs["axis"].setCurrentIndex(widget.inputs["axis"].findData("x"))
    widget.inputs["speed"].setCurrentIndex(widget.inputs["speed"].findData("speed"))
    submission = _emitted(qtbot, widget)
    assert submission.exercise_id == "fill"
    assert submission.answers == {"axis": "x", "speed": "speed"}


def test_fill_blanks_unanswered_gap_is_sent_empty(qtbot: QtBot) -> None:
    widget = FillBlanksWidget(_fill())
    qtbot.addWidget(widget)
    assert _emitted(qtbot, widget).answers == {"axis": "", "speed": ""}


def test_blank_missing_from_code_is_still_reachable(qtbot: QtBot) -> None:
    exercise = TextBlanksExercise(
        id="tb",
        skill="s",
        difficulty=1,
        prompt="?",
        code="var speed = {{value}}",
        blanks=[TextBlank(id="value"), TextBlank(id="extra")],
    )
    widget = TextBlanksWidget(exercise)
    qtbot.addWidget(widget)
    code_frame = widget.findChild(QFrame, "inlineCode")
    assert code_frame is not None
    assert code_frame.isAncestorOf(widget.inputs["extra"])
    assert widget.inputs["extra"].accessibleName() == "Lücke 2"


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
