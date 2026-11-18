from __future__ import annotations

from learnharness_protocol import Skill, SkillLevel

from learnharness_client.domain.code_questions import code_questions
from learnharness_client.domain.learning_focus import practice_candidates, suggest_focus

PLAYER = """extends CharacterBody2D

var speed = 200

func _physics_process(delta):
    velocity.x = speed  # nach rechts
    move_and_slide()
"""


def test_code_questions_for_the_player_example() -> None:
    questions = code_questions(PLAYER)
    assert questions[:3] == [
        "Was bedeutet _physics_process?",
        "Was macht velocity.x = speed?",
        "Wofür ist move_and_slide()?",
    ]
    assert len(questions) <= 4


def test_code_questions_ignore_comments_strings_and_keywords() -> None:
    questions = code_questions('if speed > 0:\n\tprint("x(1)")  # call()\nelse:\n\tpass\n')
    assert "Wann wird dieser if-Teil ausgeführt?" in questions
    assert all("call()" not in question for question in questions)
    assert all("if()" not in question for question in questions)
    assert code_questions("") == []


def test_focus_prefers_skills_that_still_need_help() -> None:
    skills = [
        Skill(id="variables", label="Variablen", level=SkillLevel.CONFIDENT),
        Skill(id="functions", label="Funktionen", level=SkillLevel.NOT_STARTED),
        Skill(id="conditions", label="Bedingungen", level=SkillLevel.WITH_HELP),
        Skill(id="loops", label="Schleifen", level=SkillLevel.ALMOST_INDEPENDENT),
    ]
    focus = suggest_focus(skills)
    assert focus is not None and focus.id == "conditions"
    assert [skill.id for skill in practice_candidates(skills)] == [
        "conditions",
        "functions",
        "loops",
    ]
    assert suggest_focus([skills[0]]) is None
