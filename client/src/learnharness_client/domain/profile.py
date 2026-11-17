"""Local pseudonymous child profiles and experience levels."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any
from uuid import uuid4


class ExperienceLevel(IntEnum):
    FIRST_STEPS = 0
    BASICS = 1
    SOME_PROJECTS = 2
    INDEPENDENT = 3


EXPERIENCE_LABELS: dict[ExperienceLevel, str] = {
    ExperienceLevel.FIRST_STEPS: "Erste Schritte",
    ExperienceLevel.BASICS: "Ich kenne die Grundlagen",
    ExperienceLevel.SOME_PROJECTS: "Ich habe schon kleine Projekte gebaut",
    ExperienceLevel.INDEPENDENT: "Ich programmiere oft selbstständig",
}


def normalize_pseudonym(value: str) -> str:
    normalized = " ".join(value.strip().split())
    if not 2 <= len(normalized) <= 30:
        raise ValueError("Der Spitzname muss zwischen 2 und 30 Zeichen lang sein.")
    if any(character in normalized for character in "\r\n\t"):
        raise ValueError("Der Spitzname enthält ungültige Zeichen.")
    return normalized


@dataclass(frozen=True, slots=True)
class StudentProfile:
    profile_id: str
    pseudonym: str
    experience_level: ExperienceLevel

    @classmethod
    def create(cls, pseudonym: str, experience_level: int) -> StudentProfile:
        return cls(
            profile_id=uuid4().hex,
            pseudonym=normalize_pseudonym(pseudonym),
            experience_level=ExperienceLevel(experience_level),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StudentProfile:
        profile_id = str(data["profile_id"])
        if not profile_id:
            raise ValueError("Die Profil-ID fehlt.")
        return cls(
            profile_id=profile_id,
            pseudonym=normalize_pseudonym(str(data["pseudonym"])),
            experience_level=ExperienceLevel(int(data["experience_level"])),
        )

    def updated(self, pseudonym: str, experience_level: int) -> StudentProfile:
        return StudentProfile(
            profile_id=self.profile_id,
            pseudonym=normalize_pseudonym(pseudonym),
            experience_level=ExperienceLevel(experience_level),
        )

    def to_dict(self) -> dict[str, str | int]:
        return {
            "profile_id": self.profile_id,
            "pseudonym": self.pseudonym,
            "experience_level": int(self.experience_level),
        }

    @property
    def experience_label(self) -> str:
        return EXPERIENCE_LABELS[self.experience_level]
