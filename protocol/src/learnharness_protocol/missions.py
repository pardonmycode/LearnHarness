"""Learning missions: a small goal split into steps the child works through."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import ProtocolModel

# understand: read an explanation and answer a question about it
# learn:      meet a new concept (e.g. a variable) with a small exercise
# exercise:   complete code; a correct answer may release generated code
# try:        try it in Godot; confirmed by the child, not checked by the server
MissionStepKind = Literal["understand", "learn", "exercise", "try"]

MISSION_ID_PATTERN = r"^[a-z0-9][a-z0-9_-]{0,63}$"


class MissionStep(ProtocolModel):
    id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    kind: MissionStepKind
    # Teacher's note for the learning server (which exercise, what to stress). The
    # administration leaves it out of the lists it sends to the app.
    note: str | None = Field(default=None, max_length=1000)


class Mission(ProtocolModel):
    type: Literal["mission"] = "mission"
    id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=120)
    goal: str
    skill: str | None = None
    steps: list[MissionStep] = Field(min_length=1, max_length=8)


class MissionList(ProtocolModel):
    """Missions the teacher assigned to a child plus the ids the child already finished."""

    type: Literal["mission_list"] = "mission_list"
    missions: list[Mission] = Field(default_factory=list)
    completed: list[str] = Field(default_factory=list)
