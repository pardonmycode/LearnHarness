"""Address comparison for the device token."""

from __future__ import annotations

from PyQt6.QtCore import QUrl


def same_server(first: str, second: str) -> bool:
    """True when both addresses point to the same scheme, host and port."""
    a, b = QUrl(first.strip()), QUrl(second.strip())
    return (
        bool(a.host())
        and a.scheme() == b.scheme()
        and a.host().casefold() == b.host().casefold()
        and a.port(-1) == b.port(-1)
    )
