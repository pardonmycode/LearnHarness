"""Small typing helpers around PyQt6 stubs."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import pyqtSignal


def signal(*types: Any) -> pyqtSignal:
    """Create a ``pyqtSignal`` for a class body.

    PyQt6 6.12's stub declares the QML-only ``arguments`` keyword without a default, so a
    plain ``pyqtSignal(object)`` fails ``mypy --strict``. The runtime call is identical.
    """
    return pyqtSignal(*types)  # type: ignore[call-arg]


# The same stub release types ``QObject.__init__(parent)`` as ``Self`` instead of
# ``QObject | None``; subclasses therefore pass ``parent`` with a narrow
# ``type: ignore[arg-type]`` marked "see qtcompat".
