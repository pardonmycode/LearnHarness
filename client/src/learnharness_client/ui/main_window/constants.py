"""Shared constants and rules of the main window."""

from __future__ import annotations

from pathlib import PurePosixPath

from learnharness_client.domain.path_guard import fold_case

MAX_FILE_CONTEXT = 16_000  # characters of the open script sent along with learn rounds


GODOT_TASK_ID = "move_player_right"


PYTHON_TASK_ID = "python_first_program"


def is_target_file(path: str, target: str | None) -> bool:
    """Generated code may only go into the file the child chose for this round."""
    if target is None:
        return False
    normalized = PurePosixPath(path.replace("\\", "/")).as_posix().removeprefix("./")
    return fold_case(normalized) == fold_case(target)
