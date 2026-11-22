"""Demo content for the fake server: code explanations, skill-focused rounds, missions.

The real learning server generates this with the language model; the fake only needs
enough content to try out every client feature without a server.
"""

from __future__ import annotations

from .explanations import (
    EXPLANATIONS,
    GENERIC_EXPLANATION,
    PYTHON_EXPLANATION,
    Explanation,
    explanation_question,
    find_explanation,
)
from .focus import FOCUS_ROUNDS, FocusRound
from .mission_parts import (
    COIN_CODE,
    DOUBLE_JUMP_CODE,
    PYTHON_GREETING_CODE,
    MissionContent,
    MissionStepContent,
    generic_mission_step,
)
from .missions import MISSIONS, find_mission
from .plans import PLAN_FIRST_QUESTION, PLAN_FOLLOW_UP, PLAN_STEPS

__all__ = [
    "COIN_CODE",
    "DOUBLE_JUMP_CODE",
    "EXPLANATIONS",
    "Explanation",
    "FOCUS_ROUNDS",
    "FocusRound",
    "GENERIC_EXPLANATION",
    "MISSIONS",
    "MissionContent",
    "MissionStepContent",
    "PLAN_FIRST_QUESTION",
    "PLAN_FOLLOW_UP",
    "PLAN_STEPS",
    "PYTHON_EXPLANATION",
    "PYTHON_GREETING_CODE",
    "explanation_question",
    "find_explanation",
    "find_mission",
    "generic_mission_step",
]
