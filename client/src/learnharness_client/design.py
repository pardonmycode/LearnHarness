"""Every value that decides how the app looks: fonts, colors, spacing and window sizes.

Change a value here and restart the app. Sizes are pixels unless a comment says otherwise.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------- Fonts
FONT_SIZE = 13  # default in points; a size the child saved in the settings wins
FONT_SIZE_MIN = 11
FONT_SIZE_MAX = 28
FONT_SMALL_MIN = 10
FONT_SMALL_OFFSET = -2  # small labels, relative to FONT_SIZE
FONT_SUBHEADING_OFFSET = 2
FONT_HEADING_OFFSET = 6
WEIGHT_SEMIBOLD = 600
WEIGHT_BOLD = 700
# Code font: the first one installed is used (Windows first, then common Linux fonts).
MONOSPACE_FONTS = (
    "Cascadia Code",
    "Cascadia Mono",
    "Consolas",
    "JetBrains Mono",
    "DejaVu Sans Mono",
    "Ubuntu Mono",
    "Noto Sans Mono",
    "Liberation Mono",
)

# --------------------------------------------------------------------------- Colors
LIGHT: dict[str, Any] = {
    "window": "#f4f6fb",
    "surface": "#ffffff",
    "surface_alt": "#eef1f7",
    "border": "#d5dbe6",
    "text": "#1d2330",
    "muted": "#5a6478",
    "accent": "#5048e5",
    "accent_hover": "#4038c9",
    "on_accent": "#ffffff",
    "accent_soft": "#ebeafd",
    "success": "#157a3d",
    "success_bg": "#e6f6ec",
    "danger": "#b42318",
    "danger_bg": "#fdecea",
    "info": "#1e4fbf",
    "info_bg": "#e8effd",
    "editor_bg": "#ffffff",
    "gutter_bg": "#f4f6fb",
    "gutter_text": "#8a93a6",
    "current_line": "#f2f4ff",
    "error_line": "#fde4e2",
    "selection": "#c9d7ff",
    "code": {
        "keyword": "#7c3aed",
        "type": "#0b6aa2",
        "number": "#b45309",
        "string": "#157a3d",
        "comment": "#6b7488",
        "annotation": "#be185d",
        "node_path": "#0f766e",
    },
}

DARK: dict[str, Any] = {
    "window": "#15171c",
    "surface": "#1d2027",
    "surface_alt": "#262a33",
    "border": "#363c48",
    "text": "#e7eaf0",
    "muted": "#a0a8b8",
    "accent": "#8c88ff",
    "accent_hover": "#a29fff",
    "on_accent": "#101022",
    "accent_soft": "#2a2950",
    "success": "#5ad68a",
    "success_bg": "#183224",
    "danger": "#ff8a80",
    "danger_bg": "#3a1d1f",
    "info": "#8cb8ff",
    "info_bg": "#1a2842",
    "editor_bg": "#1a1c22",
    "gutter_bg": "#1d2027",
    "gutter_text": "#6c7486",
    "current_line": "#232734",
    "error_line": "#41232a",
    "selection": "#3a4a78",
    "code": {
        "keyword": "#c4a7ff",
        "type": "#7cc7ff",
        "number": "#f5b971",
        "string": "#8fdc9b",
        "comment": "#8590a5",
        "annotation": "#ff8fc7",
        "node_path": "#5fd4c4",
    },
}

HIGH_CONTRAST: dict[str, Any] = {
    "window": "#000000",
    "surface": "#000000",
    "surface_alt": "#111111",
    "border": "#ffffff",
    "text": "#ffffff",
    "muted": "#e6e6e6",
    "accent": "#ffdd00",
    "accent_hover": "#ffe94d",
    "on_accent": "#000000",
    "accent_soft": "#332c00",
    "success": "#4dff88",
    "success_bg": "#002b12",
    "danger": "#ff6b6b",
    "danger_bg": "#330000",
    "info": "#7fd4ff",
    "info_bg": "#00213a",
    "editor_bg": "#000000",
    "gutter_bg": "#000000",
    "gutter_text": "#ffffff",
    "current_line": "#1a1a1a",
    "error_line": "#4d0000",
    "selection": "#0050a0",
    "code": {
        "keyword": "#ffdd00",
        "type": "#7fd4ff",
        "number": "#ffb366",
        "string": "#4dff88",
        "comment": "#c0c0c0",
        "annotation": "#ff8fd0",
        "node_path": "#66ffee",
    },
}

HIGH_CONTRAST_SELECTED_TEXT = "#000000"

# ------------------------------------------------------- Corners, borders and padding
RADIUS_LARGE = 12
RADIUS_MEDIUM = 10
RADIUS_SMALL = 8
RADIUS_TINY = 6
CALLOUT_STRIPE = 4
TAB_UNDERLINE = 3
BUTTON_PADDING = "7px 16px"
BUTTON_MIN_HEIGHT = 22
INPUT_PADDING = "6px 8px"
CALLOUT_PADDING = "10px 12px"
TAB_PADDING = "9px 16px"
LIST_PADDING = "4px"
LIST_ITEM_PADDING = "6px 4px"
TOOLTIP_PADDING = "6px"
MENU_BAR_ITEM_PADDING = "6px 12px"
MENU_ITEM_PADDING = "6px 24px 6px 16px"
DOCK_TITLE_PADDING = "6px 10px"
BADGE_PADDING = "2px 10px"
STATUS_LABEL_PADDING = "0 8px"
CHECKBOX_SPACING = 10
PROGRESS_HEIGHT = 12
SPLITTER_HANDLE = 8

# --------------------------------------------------------- Margins (left, top, right, bottom)
PANEL_MARGINS = (16, 16, 16, 16)
PANEL_SPACING = 12
PANEL_SPACING_TIGHT = 10
CARD_MARGINS = (16, 14, 16, 14)
CARD_SPACING = 8
EXERCISE_SPACING = 10
FEEDBACK_MARGINS = (12, 10, 12, 10)
FEEDBACK_SPACING = 4
FEEDBACK_ROW_SPACING = 2
PROGRESS_ROW_MARGINS = (14, 10, 14, 10)
TERMINAL_MARGINS = (8, 6, 8, 8)
TERMINAL_SPACING = 4
FIND_BAR_MARGINS = (4, 2, 4, 2)

# ------------------------------------------------------------------- Sizes of elements
PROJECT_DESCRIPTION_MIN_HEIGHT = 170
LEARN_PROMPT_HEIGHT = 90
LEVEL_CHOICE_MIN_WIDTH = 150
TUTOR_INPUT_MAX_HEIGHT = 110
TERMINAL_MIN_HEIGHT = 130
BACKUP_LIST_MAX_WIDTH = 230
TEXT_BLANK_WIDTH_CHARS = 10
EXPLAIN_CODE_EXTRA_HEIGHT = 46
EXERCISE_CODE_EXTRA_HEIGHT = 28
GUTTER_EXTRA_WIDTH = 30
GUTTER_MARK_LEFT = 8
GUTTER_NUMBER_RIGHT = 10

# ----------------------------------------------------------------- Windows and dividers
MAIN_WINDOW_SIZE = (1380, 840)
LEARNING_TABS_SHARE = 0.53  # share of the width until the child drags the divider
LEARNING_TABS_MIN_WIDTH = 320
WORK_AREA_MIN_WIDTH = 420
MAIN_STRETCH = (47, 53)  # code and terminal, learning tabs
CODE_STRETCH = (1, 4)  # script list, editor
WORK_STRETCH = (4, 1)  # code, terminal
CODE_SPLIT = (220, 700)
WORK_SPLIT = (590, 210)
CONFLICT_DIALOG_SIZE = (760, 520)
RECOVERY_DIALOG_SIZE = (700, 480)
BACKUP_DIALOG_SIZE = (900, 560)
CHANGES_DIALOG_SIZE = (1100, 620)
TEACHER_DIALOG_SIZE = (620, 440)
ADMIN_DIALOG_SIZE = (560, 300)
LOG_DIALOG_SIZE = (560, 300)
FIRST_START_MIN_WIDTH = 520
LOGIN_MIN_WIDTH = 480
TEACHER_PASSWORD_MIN_WIDTH = 420
