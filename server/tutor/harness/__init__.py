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
from .explain import EXPLAIN_FORMAT_HELP, check_explanation
from .game_blueprint import game_blueprint, is_game_project
from .learn_levels import LEVEL_KINDS, chat_topics_note, learn_topics_note, level_instructions
from .mission_code import (
    apply_typed_answers,
    check_blanks_are_clear,
    check_blanks_in_file,
    check_keeps_code,
    check_python_syntax,
)
from .mission_plan import check_mission_plan, check_open_file
from .prompts import (
    findings_text,
    history_entry,
    mission_step_context,
    system_prompt,
    topic_levels,
    user_prompt,
)
from .rules import BASE_RULES, EXPERIENCE, INTENTS, LANGUAGES, LEVELS, SKILLS
from .scene_check import SCENE_EXPLANATION, checked_scene_changes, scene_preview
from .scene_code import scene_findings
from .scene_prompt import (
    CHAT_SCENE_NOTE,
    EXPLAIN_SCENE_NOTE,
    MISSION_FILES_NOTE,
    NO_CODE_STEP_NOTE,
    REVIEW_SCENE_NOTE,
    SCENE_HEADER,
    SCENE_HELP,
    scene_help,
    scene_tree_text,
    with_scene_changes,
)
from .schemas import (
    EXERCISE_FORMAT_HELP,
    EXERCISE_SCHEMA,
    EXPLAIN_SCHEMA,
    MISSION_SCHEMA,
    PROJECT_PLAN_SCHEMA,
    PROJECT_REVIEW_SCHEMA,
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
    "EXPLAIN_FORMAT_HELP",
    "EXPLAIN_SCHEMA",
    "LEVEL_KINDS",
    "MISSION_SCHEMA",
    "MISSION_TOPICS",
    "MISSION_TOPIC_GUIDE",
    "STAGE_UP_AFTER",
    "mission_exercise_schema",
    "mission_schema",
    "has_stray_fence",
    "history_entry",
    "known_topics_note",
    "learn_exercise_schema",
    "learn_topics_note",
    "level_instructions",
    "normalize_typed",
    "reachable_topics",
    "stage_for",
    "stage_instructions",
    "PROJECT_PLAN_SCHEMA",
    "PROJECT_REVIEW_SCHEMA",
    "REPLACEMENT",
    "REVIEW_SCHEMA",
    "CHAT_SCENE_NOTE",
    "EXPLAIN_SCENE_NOTE",
    "EXPLAIN_SCENE_NOTE",
    "MISSION_FILES_NOTE",
    "REVIEW_SCENE_NOTE",
    "SCENE_HEADER",
    "findings_text",
    "scene_findings",
    "NO_CODE_STEP_NOTE",
    "SCENE_HELP",
    "SCENE_EXPLANATION",
    "checked_scene_changes",
    "scene_preview",
    "scene_help",
    "scene_tree_text",
    "with_scene_changes",
    "SKILLS",
    "StreamGuard",
    "apply_typed_answers",
    "build_exercise",
    "changed_lines",
    "chat_topics_note",
    "check_answers",
    "check_blanks_are_clear",
    "check_explanation",
    "check_blanks_in_file",
    "check_keeps_code",
    "check_kind_in_file",
    "check_mission_plan",
    "check_open_file",
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
