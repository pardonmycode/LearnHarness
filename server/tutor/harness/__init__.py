"""The harness between children and the AI.

It decides what goes out (fixed rules + level + task + the child's message, clearly marked as
data) and checks what comes back before a child sees it:

* Tutor text is filtered while it streams: code blocks or unmarked code longer than
  ``max_code_lines_in_chat`` lines are replaced by a hint, so no finished solutions arrive.
* Exercises are built by the server from structured AI output. Correct answers and the code
  that is released afterwards stay on the server (``ExerciseRecord``).
* Released code may change at most ``max_changed_lines`` lines of the child's file, and it is
  only written into the file the child is working on.
"""

from __future__ import annotations

from .checks import (
    MAX_DESCRIPTION_LENGTH,
    PLAN_ENOUGH_ANSWERS,
    PLAN_MIN_ANSWERS,
    BuiltExercise,
    HarnessRejected,
    build_exercise,
    changed_lines,
    check_answers,
    check_generated_code,
    clean_description,
)
from .game_blueprint import game_blueprint, is_game_project
from .prompts import mission_step_context, system_prompt, topic_levels, user_prompt
from .rules import BASE_RULES, EXPERIENCE, INTENTS, LANGUAGES, LEVELS, SKILLS
from .schemas import (
    EXERCISE_FORMAT_HELP,
    EXERCISE_SCHEMA,
    MISSION_SCHEMA,
    PROJECT_PLAN_SCHEMA,
    REVIEW_SCHEMA,
    mission_exercise_schema,
)
from .stream_guard import REPLACEMENT, StreamGuard, filter_text, looks_like_code
from .topics import (
    MISSION_TOPIC_GUIDE,
    MISSION_TOPICS,
    STAGE_UP_AFTER,
    normalize_typed,
    stage_for,
    stage_instructions,
)

__all__ = [
    "BASE_RULES",
    "BuiltExercise",
    "EXERCISE_FORMAT_HELP",
    "EXERCISE_SCHEMA",
    "EXPERIENCE",
    "HarnessRejected",
    "INTENTS",
    "LANGUAGES",
    "LEVELS",
    "MAX_DESCRIPTION_LENGTH",
    "PLAN_ENOUGH_ANSWERS",
    "PLAN_MIN_ANSWERS",
    "MISSION_SCHEMA",
    "MISSION_TOPICS",
    "MISSION_TOPIC_GUIDE",
    "STAGE_UP_AFTER",
    "mission_exercise_schema",
    "normalize_typed",
    "stage_for",
    "stage_instructions",
    "PROJECT_PLAN_SCHEMA",
    "REPLACEMENT",
    "REVIEW_SCHEMA",
    "SKILLS",
    "StreamGuard",
    "build_exercise",
    "changed_lines",
    "check_answers",
    "check_generated_code",
    "clean_description",
    "filter_text",
    "game_blueprint",
    "is_game_project",
    "looks_like_code",
    "mission_step_context",
    "system_prompt",
    "topic_levels",
    "user_prompt",
]
