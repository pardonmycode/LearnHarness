"""Health information exposed by the learning server."""

from __future__ import annotations

from typing import Literal

from .base import ProtocolModel


class HealthStatus(ProtocolModel):
    type: Literal["health"] = "health"
    server_ok: bool
    model_ok: bool
    session_active: bool = False
    latency_ms: int | None = None
