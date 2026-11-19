"""Design tokens, palettes and the generated application stylesheet.

All colors used anywhere in the UI come from the active :class:`ThemeColors`.
Widgets never hard-code hex values; they either rely on the stylesheet
(via object names and dynamic properties) or ask :func:`colors` at paint time.
"""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QGuiApplication, QPalette
from PyQt6.QtWidgets import QApplication, QStyleFactory, QWidget

from ..texts import T

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
_active: ThemeColors = LIGHT
_base_point_size = 14


def colors() -> ThemeColors:
    """Colors of the active theme (for custom painting and syntax highlighting)."""
    return _active


def code_color(name: str) -> QColor:
    return QColor(_active.code[name])


def base_point_size() -> int:
    return _base_point_size


def resolve_mode(mode: str) -> str:
    if mode in _THEMES:
        return mode
    hints = QGuiApplication.styleHints()
    if hints is not None and hints.colorScheme() == Qt.ColorScheme.Dark:
        return "dark"
    return "light"


def monospace_font(point_size: int | None = None) -> QFont:
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
    # Windows first, then fonts that common Linux distributions ship.
    for family in (
        "Cascadia Code",
        "Cascadia Mono",
        "Consolas",
        "JetBrains Mono",
        "DejaVu Sans Mono",
        "Ubuntu Mono",
        "Noto Sans Mono",
        "Liberation Mono",
    ):
        if family in QFontDatabase.families():
            font = QFont(family)
            break
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setPointSize(point_size or _base_point_size)
    return font


def set_state(widget: QWidget, **properties: str) -> None:
    """Set dynamic style properties and re-polish so the stylesheet picks them up."""
    for name, value in properties.items():
        widget.setProperty(name, value)
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()


def _palette(c: ThemeColors) -> QPalette:
    palette = QPalette()
    role = QPalette.ColorRole
    palette.setColor(role.Window, QColor(c.window))
    palette.setColor(role.WindowText, QColor(c.text))
    palette.setColor(role.Base, QColor(c.surface))
    palette.setColor(role.AlternateBase, QColor(c.surface_alt))
    palette.setColor(role.Text, QColor(c.text))
    palette.setColor(role.PlaceholderText, QColor(c.muted))
    palette.setColor(role.Button, QColor(c.surface))
    palette.setColor(role.ButtonText, QColor(c.text))
    palette.setColor(role.Highlight, QColor(c.selection if c is not HIGH_CONTRAST else c.accent))
    palette.setColor(role.HighlightedText, QColor(c.text if c is not HIGH_CONTRAST else "#000000"))
    palette.setColor(role.ToolTipBase, QColor(c.surface_alt))
    palette.setColor(role.ToolTipText, QColor(c.text))
    palette.setColor(role.Link, QColor(c.accent))
    palette.setColor(role.Mid, QColor(c.border))
    for group_role in (role.WindowText, role.Text, role.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, group_role, QColor(c.muted))
    return palette


def build_stylesheet(c: ThemeColors, pt: int) -> str:
    small = max(10, pt - 2)
    heading = pt + 6
    subheading = pt + 2
    return f"""
QMainWindow, QDialog {{ background: {c.window}; }}
QMenuBar, QMenu, QTreeWidget, QListWidget, QStatusBar, QHeaderView, QDockWidget,
QToolTip {{ font-size: {pt}pt; }}
QToolTip {{ background: {c.surface_alt}; color: {c.text}; border: 1px solid {c.border};
    padding: 6px; }}

QLabel[role="heading"] {{ font-size: {heading}pt; font-weight: 700; }}
QLabel[role="subheading"] {{ font-size: {subheading}pt; font-weight: 600; }}
QLabel[role="muted"] {{ color: {c.muted}; }}
QLabel[role="small"] {{ color: {c.muted}; font-size: {small}pt; }}
QLabel[role="section"] {{ color: {c.muted}; font-size: {small}pt; font-weight: 700; }}

QFrame[card="true"] {{ background: {c.surface}; border: 1px solid {c.border};
    border-radius: 12px; }}
QFrame[card="true"] QLabel {{ background: transparent; }}

QLabel[callout="neutral"], QLabel[callout="info"], QLabel[callout="success"],
QLabel[callout="error"] {{ border-radius: 10px; padding: 10px 12px; color: {c.text};
    background: {c.surface_alt}; border: 1px solid {c.border}; border-left: 4px solid {c.border}; }}
QLabel[callout="info"] {{ background: {c.info_bg}; border-color: {c.info_bg};
    border-left-color: {c.info}; }}
QLabel[callout="success"] {{ background: {c.success_bg}; border-color: {c.success_bg};
    border-left-color: {c.success}; }}
QLabel[callout="error"] {{ background: {c.danger_bg}; border-color: {c.danger_bg};
    border-left-color: {c.danger}; }}

QPushButton {{ background: {c.surface}; color: {c.text}; border: 1px solid {c.border};
    border-radius: 8px; padding: 7px 16px; min-height: 22px; }}
QPushButton:hover {{ background: {c.surface_alt}; }}
QPushButton:focus {{ border: 2px solid {c.accent}; }}
QPushButton:disabled {{ color: {c.muted}; background: {c.surface_alt}; }}
QPushButton[primary="true"] {{ background: {c.accent}; color: {c.on_accent};
    border: 1px solid {c.accent}; font-weight: 700; }}
QPushButton[primary="true"]:hover {{ background: {c.accent_hover}; }}
QPushButton[primary="true"]:disabled {{ background: {c.surface_alt}; color: {c.muted};
    border-color: {c.border}; }}

QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser, QComboBox, QSpinBox {{
    background: {c.surface}; color: {c.text}; border: 1px solid {c.border};
    border-radius: 8px; padding: 6px 8px; selection-background-color: {c.selection}; }}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border: 2px solid {c.accent}; }}
QComboBox QAbstractItemView {{ background: {c.surface}; color: {c.text};
    selection-background-color: {c.accent_soft}; selection-color: {c.text}; }}
QPlainTextEdit#codeEditor {{ background: {c.editor_bg}; border: none; border-radius: 0;
    padding: 0; }}
QPlainTextEdit#codeView {{ background: {c.editor_bg}; }}

QRadioButton, QCheckBox {{ spacing: 10px; padding: 6px 4px; }}
QRadioButton[mark="correct"], QCheckBox[mark="correct"] {{ color: {c.success};
    font-weight: 700; }}
QRadioButton[mark="wrong"], QCheckBox[mark="wrong"] {{ color: {c.danger}; font-weight: 700; }}
QLineEdit[mark="correct"], QComboBox[mark="correct"] {{ border: 2px solid {c.success}; }}
QLineEdit[mark="wrong"], QComboBox[mark="wrong"] {{ border: 2px solid {c.danger}; }}

QTabWidget::pane {{ border: none; background: {c.window}; }}
QTabBar::tab {{ background: transparent; color: {c.muted}; padding: 9px 16px;
    border: none; border-bottom: 3px solid transparent; }}
QTabBar::tab:selected {{ color: {c.text}; font-weight: 700;
    border-bottom: 3px solid {c.accent}; }}
QTabBar::tab:hover {{ color: {c.text}; }}
QTabWidget#editorTabs QTabBar::tab {{ background: {c.surface_alt}; border-radius: 0;
    margin-right: 1px; }}
QTabWidget#editorTabs QTabBar::tab:selected {{ background: {c.editor_bg}; }}

QTreeWidget, QListWidget {{ background: {c.surface}; color: {c.text};
    border: 1px solid {c.border}; border-radius: 10px; padding: 4px; outline: none; }}
QTreeWidget::item, QListWidget::item {{ padding: 6px 4px; border-radius: 6px; }}
QTreeWidget::item:hover, QListWidget::item:hover {{ background: {c.surface_alt}; }}
QTreeWidget::item:selected, QListWidget::item:selected {{ background: {c.accent_soft};
    color: {c.text}; }}
QHeaderView::section {{ background: transparent; color: {c.muted}; border: none;
    padding: 6px; font-weight: 700; }}

QProgressBar {{ background: {c.surface_alt}; border: none; border-radius: 6px;
    min-height: 12px; max-height: 12px; text-align: center; color: transparent; }}
QProgressBar::chunk {{ background: {c.accent}; border-radius: 6px; }}

QSplitter::handle {{ background: {c.window}; }}
QSplitter::handle:horizontal {{ width: 6px; }}
QDockWidget::title {{ background: {c.surface_alt}; padding: 6px 10px; }}

QStatusBar {{ background: {c.surface}; border-top: 1px solid {c.border}; color: {c.muted}; }}
QStatusBar::item {{ border: none; }}
QStatusBar QLabel {{ color: {c.muted}; padding: 0 8px; }}
QLabel#connectionBadge {{ border-radius: 10px; padding: 2px 10px; font-weight: 700; }}
QLabel#connectionBadge[state="online"] {{ background: {c.success_bg}; color: {c.success}; }}
QLabel#connectionBadge[state="offline"] {{ background: {c.danger_bg}; color: {c.danger}; }}
QLabel#connectionBadge[state="checking"] {{ background: {c.surface_alt}; color: {c.muted}; }}

QMenuBar {{ background: {c.surface}; border-bottom: 1px solid {c.border}; }}
QMenuBar::item {{ padding: 6px 12px; background: transparent; }}
QMenuBar::item:selected {{ background: {c.surface_alt}; border-radius: 6px; }}
QMenu {{ background: {c.surface}; border: 1px solid {c.border}; padding: 4px; }}
QMenu::item {{ padding: 6px 24px 6px 16px; border-radius: 6px; }}
QMenu::item:selected {{ background: {c.accent_soft}; color: {c.text}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
"""


def apply_theme(app: QApplication, font_size: int = 14, mode: str = "system") -> ThemeColors:
    """Apply palette, font and stylesheet. Returns the colors that are now active."""
    global _active, _base_point_size
    _base_point_size = max(11, min(28, font_size))
    _active = _THEMES[resolve_mode(mode)]
    fusion = QStyleFactory.create("Fusion")
    if fusion is not None:
        app.setStyle(fusion)
    font = app.font()
    font.setPointSize(_base_point_size)
    app.setFont(font)
    app.setPalette(_palette(_active))
    app.setStyleSheet(build_stylesheet(_active, _base_point_size))
    return _active
