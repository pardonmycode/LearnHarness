"""Color sets of the themes."""

from __future__ import annotations

from dataclasses import dataclass

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


LIGHT = ThemeColors(
    window="#f4f6fb",
    surface="#ffffff",
    surface_alt="#eef1f7",
    border="#d5dbe6",
    text="#1d2330",
    muted="#5a6478",
    accent="#5048e5",
    accent_hover="#4038c9",
    on_accent="#ffffff",
    accent_soft="#ebeafd",
    success="#157a3d",
    success_bg="#e6f6ec",
    danger="#b42318",
    danger_bg="#fdecea",
    info="#1e4fbf",
    info_bg="#e8effd",
    editor_bg="#ffffff",
    gutter_bg="#f4f6fb",
    gutter_text="#8a93a6",
    current_line="#f2f4ff",
    error_line="#fde4e2",
    selection="#c9d7ff",
    code={
        "keyword": "#7c3aed",
        "type": "#0b6aa2",
        "number": "#b45309",
        "string": "#157a3d",
        "comment": "#6b7488",
        "annotation": "#be185d",
        "node_path": "#0f766e",
    },
)


DARK = ThemeColors(
    window="#15171c",
    surface="#1d2027",
    surface_alt="#262a33",
    border="#363c48",
    text="#e7eaf0",
    muted="#a0a8b8",
    accent="#8c88ff",
    accent_hover="#a29fff",
    on_accent="#101022",
    accent_soft="#2a2950",
    success="#5ad68a",
    success_bg="#183224",
    danger="#ff8a80",
    danger_bg="#3a1d1f",
    info="#8cb8ff",
    info_bg="#1a2842",
    editor_bg="#1a1c22",
    gutter_bg="#1d2027",
    gutter_text="#6c7486",
    current_line="#232734",
    error_line="#41232a",
    selection="#3a4a78",
    code={
        "keyword": "#c4a7ff",
        "type": "#7cc7ff",
        "number": "#f5b971",
        "string": "#8fdc9b",
        "comment": "#8590a5",
        "annotation": "#ff8fc7",
        "node_path": "#5fd4c4",
    },
)


HIGH_CONTRAST = ThemeColors(
    window="#000000",
    surface="#000000",
    surface_alt="#111111",
    border="#ffffff",
    text="#ffffff",
    muted="#e6e6e6",
    accent="#ffdd00",
    accent_hover="#ffe94d",
    on_accent="#000000",
    accent_soft="#332c00",
    success="#4dff88",
    success_bg="#002b12",
    danger="#ff6b6b",
    danger_bg="#330000",
    info="#7fd4ff",
    info_bg="#00213a",
    editor_bg="#000000",
    gutter_bg="#000000",
    gutter_text="#ffffff",
    current_line="#1a1a1a",
    error_line="#4d0000",
    selection="#0050a0",
    code={
        "keyword": "#ffdd00",
        "type": "#7fd4ff",
        "number": "#ffb366",
        "string": "#4dff88",
        "comment": "#c0c0c0",
        "annotation": "#ff8fd0",
        "node_path": "#66ffee",
    },
)


_THEMES = {"light": LIGHT, "dark": DARK, "high_contrast": HIGH_CONTRAST}
