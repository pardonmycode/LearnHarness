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


class MissionStep(ProtocolModel):
    id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    kind: MissionStepKind


class Mission(ProtocolModel):
    type: Literal["mission"] = "mission"
    id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=120)
    goal: str
    skill: str | None = None
    steps: list[MissionStep] = Field(min_length=1, max_length=8)
