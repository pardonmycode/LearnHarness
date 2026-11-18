"""Central child profiles managed by the LearnHarness admin server (Django)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from .base import ProtocolModel

MIN_LEARNING_LEVEL = 1
MAX_LEARNING_LEVEL = 10


def _normalize_pseudonym(value: str) -> str:
    normalized = " ".join(value.split())
    if not 2 <= len(normalized) <= 30:
        raise ValueError("Der Spitzname muss 2 bis 30 Zeichen lang sein")
    return normalized


class ChildProfile(ProtocolModel):
    """A pseudonymous child. Real names are deliberately not part of the protocol."""

    type: Literal["child_profile"] = "child_profile"
    profile_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    pseudonym: str
    experience_level: int = Field(ge=0, le=3)
    max_level: int = Field(
        default=MIN_LEARNING_LEVEL, ge=MIN_LEARNING_LEVEL, le=MAX_LEARNING_LEVEL
    )
    group: str | None = None

    _check_pseudonym = field_validator("pseudonym")(_normalize_pseudonym)


class ChildProfileList(ProtocolModel):
    type: Literal["child_profile_list"] = "child_profile_list"
    profiles: list[ChildProfile] = Field(default_factory=list)


class ChildProfileUpdate(ProtocolModel):
    """Changes a client may make; the level is changed only via LevelUnlock."""

    type: Literal["child_profile_update"] = "child_profile_update"
    pseudonym: str | None = None
    experience_level: int | None = Field(default=None, ge=0, le=3)

    @field_validator("pseudonym")
    @classmethod
    def _check_pseudonym(cls, value: str | None) -> str | None:
        return None if value is None else _normalize_pseudonym(value)


class LevelUnlock(ProtocolModel):
    """Clients may only raise the level; lowering it is reserved for teachers."""

    type: Literal["level_unlock"] = "level_unlock"
    level: int = Field(ge=MIN_LEARNING_LEVEL, le=MAX_LEARNING_LEVEL)
