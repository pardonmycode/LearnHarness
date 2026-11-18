"""Shared test setup: headless Qt with real system fonts."""

from __future__ import annotations

import os
from pathlib import Path


def _system_font_dir() -> Path | None:
    candidates = [
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
        Path("/usr/share/fonts"),
        Path("/System/Library/Fonts"),
    ]
    return next((path for path in candidates if path.is_dir()), None)


# Must run before pytest-qt creates the QApplication.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_fonts = _system_font_dir()
if _fonts is not None:
    os.environ.setdefault("QT_QPA_FONTDIR", str(_fonts))
