"""Palettes and the generated application stylesheet; the values live in ``design.py``.

All colors used anywhere in the UI come from the active :class:`ThemeColors`.
Widgets never hard-code hex values; they either rely on the stylesheet
(via object names and dynamic properties) or ask :func:`colors` at paint time.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QGuiApplication
from PyQt6.QtWidgets import QApplication, QStyleFactory, QWidget

from learnharness_client import design

from .palettes import _THEMES, DARK, HIGH_CONTRAST, LIGHT, THEME_CHOICES, ThemeColors
from .stylesheet import _palette, build_stylesheet

__all__ = [
    "DARK",
    "HIGH_CONTRAST",
    "LIGHT",
    "THEME_CHOICES",
    "ThemeColors",
    "apply_theme",
    "base_point_size",
    "build_stylesheet",
    "code_color",
    "colors",
    "monospace_font",
    "resolve_mode",
    "set_state",
]


_active: ThemeColors = LIGHT


_base_point_size = design.FONT_SIZE


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
    for family in design.MONOSPACE_FONTS:
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


def apply_theme(
    app: QApplication, font_size: int = design.FONT_SIZE, mode: str = "system"
) -> ThemeColors:
    """Apply palette, font and stylesheet. Returns the colors that are now active."""
    global _active, _base_point_size
    _base_point_size = max(design.FONT_SIZE_MIN, min(design.FONT_SIZE_MAX, font_size))
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
