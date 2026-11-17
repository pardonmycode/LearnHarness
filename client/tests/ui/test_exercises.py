from __future__ import annotations

from learnharness_protocol import (
    Blank,
    Choice,
    FillBlanksExercise,
    MultipleChoiceExercise,
    ReviewResult,
    TextBlank,
    TextBlanksExercise,
)
from pytestqt.qtbot import QtBot

from learnharness_client.ui.exercises.fill_blanks import FillBlanksWidget
from learnharness_client.ui.exercises.multiple_choice import MultipleChoiceWidget
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
