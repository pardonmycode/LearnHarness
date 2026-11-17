"""Base types and protocol-version checks."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

PROTOCOL_VERSION = "1.1"


def protocol_major(version: str) -> str:
    """Return the major component or reject an empty version."""
    major = version.partition(".")[0].strip()
    if not major.isdigit():
        raise ValueError("Ungültige Protokollversion")
    return major


class ProtocolModel(BaseModel):
    """Strict base model used for every network payload."""

    model_config = ConfigDict(extra="forbid")

    protocol_version: str = PROTOCOL_VERSION

    @field_validator("protocol_version")
    @classmethod
    def validate_protocol_version(cls, value: str) -> str:
        if protocol_major(value) != protocol_major(PROTOCOL_VERSION):
            raise ValueError(
                f"Protokollversion {value} ist nicht mit {PROTOCOL_VERSION} kompatibel"
            )
        return value
