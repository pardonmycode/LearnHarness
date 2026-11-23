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
from .code_fence import has_stray_fence, unwrap_code_fence
from .exercise_kinds import check_kind_in_file
from .game_blueprint import game_blueprint, is_game_project
from .learn_levels import LEVEL_KINDS, learn_topics_note, level_instructions
from .mission_code import (
    apply_typed_answers,
    check_blanks_are_clear,
    check_blanks_in_file,
    check_keeps_code,
    check_python_syntax,
)
from .mission_plan import check_mission_plan
from .prompts import mission_step_context, system_prompt, topic_levels, user_prompt
from .rules import BASE_RULES, EXPERIENCE, INTENTS, LANGUAGES, LEVELS, SKILLS
from .schemas import (
    EXERCISE_FORMAT_HELP,
    EXERCISE_SCHEMA,
    MISSION_SCHEMA,
    PROJECT_PLAN_SCHEMA,
    REVIEW_SCHEMA,
    learn_exercise_schema,
    mission_exercise_schema,
    mission_schema,
)
from .stream_guard import REPLACEMENT, StreamGuard, filter_text, looks_like_code
from .topics import (
    MISSION_TOPIC_GUIDE,
    MISSION_TOPICS,
    STAGE_UP_AFTER,
    known_topics_note,
    normalize_typed,
    reachable_topics,
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
    "LEVEL_KINDS",
    "MISSION_SCHEMA",
    "MISSION_TOPICS",
    "MISSION_TOPIC_GUIDE",
    "STAGE_UP_AFTER",
    "mission_exercise_schema",
    "mission_schema",
    "has_stray_fence",
    "known_topics_note",
    "learn_exercise_schema",
    "learn_topics_note",
    "level_instructions",
    "normalize_typed",
    "reachable_topics",
    "stage_for",
    "stage_instructions",
    "PROJECT_PLAN_SCHEMA",
    "REPLACEMENT",
    "REVIEW_SCHEMA",
    "SKILLS",
    "StreamGuard",
    "apply_typed_answers",
    "build_exercise",
    "changed_lines",
    "check_answers",
    "check_blanks_are_clear",
    "check_blanks_in_file",
    "check_keeps_code",
    "check_kind_in_file",
    "check_mission_plan",
    "check_python_syntax",
    "check_generated_code",
    "clean_description",
    "filter_text",
    "game_blueprint",
    "is_game_project",
    "looks_like_code",
    "mission_step_context",
    "system_prompt",
    "topic_levels",
    "unwrap_code_fence",
    "user_prompt",
]
