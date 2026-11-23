"""Color sets of the themes."""

from __future__ import annotations

from dataclasses import dataclass

from learnharness_client import design

from ...texts import T

THEME_CHOICES: list[tuple[str, str]] = [
    ("system", T.THEME_SYSTEM),
    ("light", T.THEME_LIGHT),
    ("dark", T.THEME_DARK),
    ("high_contrast", T.THEME_HIGH_CONTRAST),
]


@dataclass(frozen=True, slots=True)
class ThemeColors:
    window: str
    surface: str
    surface_alt: str
    border: str
    text: str
    muted: str
    accent: str
    accent_hover: str
    on_accent: str
    accent_soft: str
    success: str
    success_bg: str
    danger: str
    danger_bg: str
    info: str
    info_bg: str
    editor_bg: str
    gutter_bg: str
    gutter_text: str
    current_line: str
    error_line: str
    selection: str
    code: dict[str, str]


LIGHT = ThemeColors(**design.LIGHT)
DARK = ThemeColors(**design.DARK)
HIGH_CONTRAST = ThemeColors(**design.HIGH_CONTRAST)


_THEMES = {"light": LIGHT, "dark": DARK, "high_contrast": HIGH_CONTRAST}
