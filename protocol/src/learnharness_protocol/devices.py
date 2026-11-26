"""A PC asks the administration for access; a teacher approves it in the admin.

The PC makes its own random token and sends it with the request. The server only keeps its
hash and turns it into a normal device access once a teacher approves, so no token ever has
to be shown or typed. A four-digit code on both screens shows that the right PC is approved.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from .base import ProtocolModel

DeviceRequestState = Literal["pending", "approved", "rejected", "expired"]


class DeviceRequestCreate(ProtocolModel):
    type: Literal["device_request"] = "device_request"
    # Typed by the teacher, e.g. "PC 3"; the computer's own name often holds a real name.
    name: str = Field(min_length=2, max_length=40)
    token: str = Field(min_length=32, max_length=200, pattern=r"^[A-Za-z0-9_\-]+$")

    @field_validator("name")
    @classmethod
    def plain_name(cls, value: str) -> str:
        clean = " ".join(value.split())
        if len(clean) < 2 or any(not char.isprintable() for char in clean):
            raise ValueError("Bitte einen kurzen Namen wie „PC 3“ eintragen.")
        return clean


class DeviceRequestStatus(ProtocolModel):
    type: Literal["device_request_status"] = "device_request_status"
    request_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    code: str = Field(pattern=r"^\d{4}$")
    status: DeviceRequestState
