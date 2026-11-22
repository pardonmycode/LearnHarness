"""Qt palette and stylesheet built from a color set."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette

from .palettes import HIGH_CONTRAST, ThemeColors


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
