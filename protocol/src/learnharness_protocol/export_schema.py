"""Write the public JSON schemas for server implementers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from pydantic import TypeAdapter

from .exercises import Exercise, ReviewResult, Submission
from .health import HealthStatus
from .messages import LearningResponse, SessionCreate, StudentMessage
from .missions import Mission
from .profiles import ChildProfile, ChildProfileList, ChildProfileUpdate, LevelUnlock
from .progress import ProgressUpdate


def export_schemas(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    exercise_adapter = TypeAdapter[Exercise](cast(Any, Exercise))
    schemas: dict[str, dict[str, object]] = {
        "child_profile": ChildProfile.model_json_schema(),
        "child_profile_list": ChildProfileList.model_json_schema(),
        "child_profile_update": ChildProfileUpdate.model_json_schema(),
        "exercise": exercise_adapter.json_schema(),
        "health_status": HealthStatus.model_json_schema(),
        "learning_response": LearningResponse.model_json_schema(),
        "mission": Mission.model_json_schema(),
        "level_unlock": LevelUnlock.model_json_schema(),
        "progress_update": ProgressUpdate.model_json_schema(),
        "review_result": ReviewResult.model_json_schema(),
        "session_create": SessionCreate.model_json_schema(),
        "student_message": StudentMessage.model_json_schema(),
        "submission": Submission.model_json_schema(),
    }
    for name, schema in schemas.items():
        (destination / f"{name}.schema.json").write_text(
            json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    export_schemas(Path("schemas"))
