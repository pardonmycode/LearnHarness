"""Learning progress by skill, deliberately without a total score."""

from __future__ import annotations

from enum import IntEnum
from typing import Literal

from pydantic import Field

from .base import ProtocolModel


class SkillLevel(IntEnum):
    NOT_STARTED = 0
    WITH_HELP = 1
    ALMOST_INDEPENDENT = 2
    CONFIDENT = 3


class Skill(ProtocolModel):
    id: str
    label: str
    level: SkillLevel


class ProgressUpdate(ProtocolModel):
    type: Literal["progress_update"] = "progress_update"
    skills: list[Skill] = Field(default_factory=list)
