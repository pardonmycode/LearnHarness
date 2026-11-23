"""The mission tab always shows one clear next action."""

from __future__ import annotations

from learnharness_protocol import (
    LearningResponse,
    Mission,
    MissionStep,
    MultipleChoiceExercise,
    ReviewResult,
)
from learnharness_protocol.exercises import Choice
from pytestqt.qtbot import QtBot

from learnharness_client.texts import T
from learnharness_client.ui.panels.mission_panel import MissionPanel


def _panel(qtbot: QtBot) -> tuple[MissionPanel, list[str]]:
    panel = MissionPanel()
    qtbot.addWidget(panel)
    requested: list[str] = []
    panel.step_requested.connect(lambda _mission, step: requested.append(step))
    panel.show_mission(
        Mission(
            id="m",
            title="Mission",
            goal="Ziel",
            steps=[
                MissionStep(id="a", title="Lesen", kind="understand"),
                MissionStep(id="b", title="Üben", kind="exercise"),
                MissionStep(id="c", title="Ausprobieren", kind="try"),
            ],
        )
    )
    panel.show()
    return panel, requested


def _exercise() -> MultipleChoiceExercise:
    return MultipleChoiceExercise(
        id="e",
        skill="Mission",
        difficulty=1,
        prompt="Frage?",
        choices=[Choice(id="right", text="Ja"), Choice(id="wrong", text="Nein")],
    )


def _explanation(text: str = "Das ist die Erklärung.") -> LearningResponse:
    return LearningResponse(mode="explanation", message=text)


def test_button_names_the_step_and_hides_while_answering(qtbot: QtBot) -> None:
    panel, requested = _panel(qtbot)
    assert panel.step_button.text() == "Schritt 1 starten: Lesen"
    panel.step_button.click()
    assert requested == ["a"] and not panel.step_button.isVisible()
    panel.show_step_response(LearningResponse(mode="exercise", message="Los", exercise=_exercise()))
    assert not panel.step_button.isVisible() and panel.answer_hint.isVisible()
    panel.step_button.click()  # hidden: must not throw the open exercise away
    assert requested == ["a"] and panel.exercises.current is not None


def test_explanation_stays_until_understood(qtbot: QtBot) -> None:
    panel, requested = _panel(qtbot)
    panel.step_button.click()
    panel.show_step_response(_explanation())
    assert "a" not in panel.done
    assert panel.message.text() == "Das ist die Erklärung."
    assert panel.step_button.text() == T.MISSION_UNDERSTOOD
    panel.step_button.click()
    assert "a" in panel.done and requested == ["a", "b"]


def test_wrong_answer_stays_right_answer_offers_next(qtbot: QtBot) -> None:
    panel, requested = _panel(qtbot)
    panel.step_button.click()
    panel.show_step_response(_explanation())
    panel.step_button.click()
    panel.show_step_response(LearningResponse(mode="exercise", message="Los", exercise=_exercise()))
    panel.show_review(ReviewResult(correct=False, feedback="Nein"))
    assert "b" not in panel.done and not panel.step_button.isVisible()
    panel.show_review(ReviewResult(correct=True, feedback="Super erklärt."))
    assert panel.message.text() == T.MISSION_STEP_DONE  # feedback stays in the exercise
    assert panel.step_button.text().startswith("Weiter zu Schritt 3: Ausprobieren")
    assert requested == ["a", "b"]  # the next step never starts by itself


def test_try_step_has_help_and_offers_the_next_project_mission(qtbot: QtBot) -> None:
    panel, _requested = _panel(qtbot)
    help_clicks: list[bool] = []
    wishes: list[str] = []
    panel.help_requested.connect(lambda: help_clicks.append(True))
    panel.mission_requested.connect(wishes.append)
    panel.set_project_idea(True)
    panel.done = {"a", "b"}
    panel._render()
    assert panel.step_button.text() == T.MISSION_TRY_WORKED
    panel.help_button.click()
    assert help_clicks and not panel.complete
    panel.step_button.click()
    assert panel.complete and not panel.step_button.isVisible()
    assert panel.next_project_button.isVisible()
    panel.next_project_button.click()
    assert panel.mission is None and wishes == [T.MISSION_PROJECT_WISH]


def test_failed_start_offers_the_same_step_again(qtbot: QtBot) -> None:
    panel, requested = _panel(qtbot)
    panel.step_button.click()
    panel.show_error("Der Lernhelfer macht Pause.")
    assert panel.step_button.isVisible() and panel.step_button.text().startswith("Schritt 1")
    panel.step_button.click()
    assert requested == ["a", "a"]


def test_restored_mission_shows_where_to_continue(qtbot: QtBot) -> None:
    panel, _requested = _panel(qtbot)
    panel.done = {"a"}
    panel._emit_progress()
    restored = MissionPanel()
    qtbot.addWidget(restored)
    restored.restore(panel.state())
    assert restored.step_button.text() == "Schritt 2 starten: Üben"
