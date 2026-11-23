"""Each LearnAgent level has its own kind of exercise, checked by the server."""

from __future__ import annotations

from typing import Any

import pytest
from learnharness_protocol import (
    FillBlanksExercise,
    FindBugExercise,
    LearningResponse,
    MultipleChoiceExercise,
    OrderingExercise,
    StudentMessage,
    Submission,
    TextBlanksExercise,
)
from tutor_helpers import ScriptedProvider

from tutor import engine, harness
from tutor.models import AiSettings, TutorSession

BEFORE = "muenzen = 0\n"
LINES = ["muenzen = 0", "for i in range(5):", "    muenzen += 1"]
GOOD = "muenzen = 0\n# Zaehlt\nfor i in range(5):\n    # Eine mehr\n    muenzen += 1\n"


def _base(kind: str, **extra: Any) -> dict[str, Any]:
    return {
        "message": "Los",
        "skill": "loops",
        "kind": kind,
        "prompt": "Der Fuchs zählt fünf Münzen.",
        "code": "",
        "choices": [],
        "blanks": [],
        "explanation_after_correct": "Gut",
        "new_file_content": GOOD,
    } | extra


ANSWERS = {
    "multiple_choice": {
        "choices": [{"text": "a", "correct": True}, {"text": "b", "correct": False}]
    },
    "fill_blanks": {
        "code": "for i in {{1}}(5):",
        "blanks": [{"options": ["range", "print"], "answer": "range"}],
    },
    "ordering": {"ordered_lines": LINES},
    "text_blanks": {
        "code": "for i in {{1}}:",
        "blanks": [{"answer": "range(5)", "alternatives": ["range(0, 5)"]}],
    },
    "find_bug": {
        "buggy_lines": ["muenzen = 0", "for i in range(4):", "    muenzen += 1"],
        "bug_line": 2,
    },
}
TYPES = {
    "multiple_choice": MultipleChoiceExercise,
    "fill_blanks": FillBlanksExercise,
    "ordering": OrderingExercise,
    "text_blanks": TextBlanksExercise,
    "find_bug": FindBugExercise,
}


def _message(session: TutorSession, level: int) -> StudentMessage:
    return StudentMessage(
        intent="learn",
        language="python",
        session_id=session.id,
        project_id="spiel",
        learning_level=level,
        file="main.py",
        code_excerpt=BEFORE,
        message="Der Fuchs soll fünf Münzen zählen",
    )


def _run(session: TutorSession, scripted: dict[str, ScriptedProvider], level: int, *answers: Any):
    scripted["provider"] = ScriptedProvider(json_answers=list(answers))
    tutor = engine.Tutor(session)
    return tutor, tutor.handle(_message(session, level))


@pytest.mark.django_db
@pytest.mark.parametrize("level", range(1, 11))
def test_every_level_gets_its_kind(
    session: TutorSession, scripted: dict[str, ScriptedProvider], level: int
) -> None:
    kind = harness.LEVEL_KINDS[level]
    _, response = _run(session, scripted, level, _base(kind, **ANSWERS[kind]))
    assert isinstance(response, LearningResponse)
    assert isinstance(response.exercise, TYPES[kind])
    assert f'"kind": "{kind}"' in scripted["provider"].calls[0][0].replace('"kind":\n', '"kind": ')
    assert harness.learn_exercise_schema(level)["properties"]["kind"]["enum"] == [kind]


@pytest.mark.django_db
def test_wrong_kind_for_the_level_is_rejected(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    wrong = _base("fill_blanks", **ANSWERS["fill_blanks"])
    right = _base("multiple_choice", **ANSWERS["multiple_choice"])
    _, response = _run(session, scripted, 1, wrong, right)
    assert isinstance(response.exercise, MultipleChoiceExercise)
    assert len(scripted["provider"].calls) == 2


@pytest.mark.django_db
def test_ordering_is_shuffled_and_checked(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    tutor, response = _run(session, scripted, 5, _base("ordering", **ANSWERS["ordering"]))
    exercise = response.exercise
    assert [item.text for item in exercise.items] != LINES
    by_text = {item.text: item.id for item in exercise.items}
    wrong = [item.id for item in exercise.items]
    assert (
        tutor.review_submission(
            Submission(exercise_id=exercise.id, answers={"order": wrong})
        ).correct
        is False
    )
    right = [by_text[line] for line in LINES]
    review = tutor.review_submission(Submission(exercise_id=exercise.id, answers={"order": right}))
    assert review.correct is True and review.generated_files[0].content == GOOD


@pytest.mark.django_db
def test_find_bug_is_checked_and_does_not_release_the_bug(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    keeps_bug = GOOD.replace("range(5):", "range(4):")
    good = _base("find_bug", **ANSWERS["find_bug"])
    tutor, response = _run(session, scripted, 8, good | {"new_file_content": keeps_bug}, good)
    assert "falsche Zeile" in scripted["provider"].calls[1][1][-1]["content"]
    exercise = response.exercise
    assert (
        tutor.review_submission(Submission(exercise_id=exercise.id, answers={"lines": [1]})).correct
        is False
    )
    assert (
        tutor.review_submission(Submission(exercise_id=exercise.id, answers={"lines": [2]})).correct
        is True
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("level", "kind", "change", "reason"),
    [
        (3, "fill_blanks", {"new_file_content": "muenzen = 0\nprint(muenzen)\n"}, "fehlt"),
        (6, "text_blanks", {"prompt": "Nutze range(5)."}, "verraten"),
        (5, "ordering", {"new_file_content": "muenzen = 0\nprint(muenzen)\n"}, "Reihenfolge"),
    ],
)
def test_learn_has_the_mission_guards(
    session: TutorSession,
    scripted: dict[str, ScriptedProvider],
    level: int,
    kind: str,
    change: dict[str, str],
    reason: str,
) -> None:
    good = _base(kind, **ANSWERS[kind])
    _, response = _run(session, scripted, level, good | change, good)
    assert isinstance(response, LearningResponse)
    assert reason in scripted["provider"].calls[1][1][-1]["content"]


@pytest.mark.django_db
def test_prompt_knows_the_childs_topics(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    session.child.set_skill("variables", "Variablen", 2)
    _run(session, scripted, 1, _base("multiple_choice", **ANSWERS["multiple_choice"]))
    system, messages = scripted["provider"].calls[0]
    assert "kennt das Kind schon: variables." in messages[0]["content"]
    assert "Nutze in der Übung die" in system and "weiter starten" in system
    settings = AiSettings.load()
    assert "Reihenfolge" in harness.system_prompt("learn", settings, learning_level=5)
