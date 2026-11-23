"""Qt palette and stylesheet built from a color set."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette

from learnharness_client import design as d

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
    selected_text = d.HIGH_CONTRAST_SELECTED_TEXT if c is HIGH_CONTRAST else c.text
    palette.setColor(role.HighlightedText, QColor(selected_text))
    palette.setColor(role.ToolTipBase, QColor(c.surface_alt))
    palette.setColor(role.ToolTipText, QColor(c.text))
    palette.setColor(role.Link, QColor(c.accent))
    palette.setColor(role.Mid, QColor(c.border))
    for group_role in (role.WindowText, role.Text, role.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, group_role, QColor(c.muted))
    return palette


def build_stylesheet(c: ThemeColors, pt: int) -> str:
    small = max(d.FONT_SMALL_MIN, pt + d.FONT_SMALL_OFFSET)
    heading = pt + d.FONT_HEADING_OFFSET
    subheading = pt + d.FONT_SUBHEADING_OFFSET
    return f"""
QMainWindow, QDialog {{ background: {c.window}; }}
QMenuBar, QMenu, QTreeWidget, QListWidget, QStatusBar, QHeaderView, QDockWidget,
QToolTip {{ font-size: {pt}pt; }}
QToolTip {{ background: {c.surface_alt}; color: {c.text}; border: 1px solid {c.border};
    padding: {d.TOOLTIP_PADDING}; }}

QLabel[role="heading"] {{ font-size: {heading}pt; font-weight: {d.WEIGHT_BOLD}; }}
QLabel[role="subheading"] {{ font-size: {subheading}pt; font-weight: {d.WEIGHT_SEMIBOLD}; }}
QLabel[role="muted"] {{ color: {c.muted}; }}
QLabel[role="small"] {{ color: {c.muted}; font-size: {small}pt; }}
QLabel[role="section"] {{ color: {c.muted}; font-size: {small}pt; font-weight: {d.WEIGHT_BOLD}; }}

QFrame[card="true"] {{ background: {c.surface}; border: 1px solid {c.border};
    border-radius: {d.RADIUS_LARGE}px; }}
QFrame[card="true"] QLabel {{ background: transparent; }}

QLabel[callout="neutral"], QLabel[callout="info"], QLabel[callout="success"],
QLabel[callout="error"] {{ border-radius: {d.RADIUS_MEDIUM}px; padding: {d.CALLOUT_PADDING};
    color: {c.text};
    background: {c.surface_alt}; border: 1px solid {c.border};
    border-left: {d.CALLOUT_STRIPE}px solid {c.border}; }}
QLabel[callout="info"] {{ background: {c.info_bg}; border-color: {c.info_bg};
    border-left-color: {c.info}; }}
QLabel[callout="success"] {{ background: {c.success_bg}; border-color: {c.success_bg};
    border-left-color: {c.success}; }}
QLabel[callout="error"] {{ background: {c.danger_bg}; border-color: {c.danger_bg};
    border-left-color: {c.danger}; }}

QPushButton {{ background: {c.surface}; color: {c.text}; border: 1px solid {c.border};
    border-radius: {d.RADIUS_SMALL}px; padding: {d.BUTTON_PADDING};
    min-height: {d.BUTTON_MIN_HEIGHT}px; }}
QPushButton:hover {{ background: {c.surface_alt}; }}
QPushButton:focus {{ border: 2px solid {c.accent}; }}
QPushButton:disabled {{ color: {c.muted}; background: {c.surface_alt}; }}
QPushButton[primary="true"] {{ background: {c.accent}; color: {c.on_accent};
    border: 1px solid {c.accent}; font-weight: {d.WEIGHT_BOLD}; }}
QPushButton[primary="true"]:hover {{ background: {c.accent_hover}; }}
QPushButton[primary="true"]:disabled {{ background: {c.surface_alt}; color: {c.muted};
    border-color: {c.border}; }}

QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser, QComboBox, QSpinBox {{
    background: {c.surface}; color: {c.text}; border: 1px solid {c.border};
    border-radius: {d.RADIUS_SMALL}px; padding: {d.INPUT_PADDING};
    selection-background-color: {c.selection}; }}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border: 2px solid {c.accent}; }}
QComboBox QAbstractItemView {{ background: {c.surface}; color: {c.text};
    selection-background-color: {c.accent_soft}; selection-color: {c.text}; }}
QPlainTextEdit#codeEditor {{ background: {c.editor_bg}; border: none; border-radius: 0;
    padding: 0; }}
QPlainTextEdit#codeView {{ background: {c.editor_bg}; }}

QRadioButton, QCheckBox {{ spacing: {d.CHECKBOX_SPACING}px; padding: {d.LIST_ITEM_PADDING}; }}
QRadioButton[mark="correct"], QCheckBox[mark="correct"] {{ color: {c.success};
    font-weight: {d.WEIGHT_BOLD}; }}
QRadioButton[mark="wrong"], QCheckBox[mark="wrong"] {{ color: {c.danger};
    font-weight: {d.WEIGHT_BOLD}; }}
QLineEdit[mark="correct"], QComboBox[mark="correct"] {{ border: 2px solid {c.success}; }}
QLineEdit[mark="wrong"], QComboBox[mark="wrong"] {{ border: 2px solid {c.danger}; }}

QTabWidget::pane {{ border: none; background: {c.window}; }}
QTabBar::tab {{ background: transparent; color: {c.muted}; padding: {d.TAB_PADDING};
    border: none; border-bottom: {d.TAB_UNDERLINE}px solid transparent; }}
QTabBar::tab:selected {{ color: {c.text}; font-weight: {d.WEIGHT_BOLD};
    border-bottom: {d.TAB_UNDERLINE}px solid {c.accent}; }}
QTabBar::tab:hover {{ color: {c.text}; }}
QTabWidget#editorTabs QTabBar::tab {{ background: {c.surface_alt}; border-radius: 0;
    margin-right: 1px; }}
QTabWidget#editorTabs QTabBar::tab:selected {{ background: {c.editor_bg}; }}

QTreeWidget, QListWidget {{ background: {c.surface}; color: {c.text};
    border: 1px solid {c.border}; border-radius: {d.RADIUS_MEDIUM}px; padding: {d.LIST_PADDING};
    outline: none; }}
QTreeWidget::item, QListWidget::item {{ padding: {d.LIST_ITEM_PADDING};
    border-radius: {d.RADIUS_TINY}px; }}
QTreeWidget::item:hover, QListWidget::item:hover {{ background: {c.surface_alt}; }}
QTreeWidget::item:selected, QListWidget::item:selected {{ background: {c.accent_soft};
    color: {c.text}; }}
QHeaderView::section {{ background: transparent; color: {c.muted}; border: none;
    padding: {d.TOOLTIP_PADDING}; font-weight: {d.WEIGHT_BOLD}; }}

QProgressBar {{ background: {c.surface_alt}; border: none; border-radius: {d.RADIUS_TINY}px;
    min-height: {d.PROGRESS_HEIGHT}px; max-height: {d.PROGRESS_HEIGHT}px; text-align: center;
    color: transparent; }}
QProgressBar::chunk {{ background: {c.accent}; border-radius: {d.RADIUS_TINY}px; }}

QSplitter::handle {{ background: {c.window}; }}
QSplitter::handle:hover {{ background: {c.accent_soft}; }}
QSplitter::handle:pressed {{ background: {c.accent}; }}
QSplitter::handle:horizontal {{ width: {d.SPLITTER_HANDLE}px; }}
QSplitter::handle:vertical {{ height: {d.SPLITTER_HANDLE}px; }}
QDockWidget::title {{ background: {c.surface_alt}; padding: {d.DOCK_TITLE_PADDING}; }}

QStatusBar {{ background: {c.surface}; border-top: 1px solid {c.border}; color: {c.muted}; }}
QStatusBar::item {{ border: none; }}
QStatusBar QLabel {{ color: {c.muted}; padding: {d.STATUS_LABEL_PADDING}; }}
QLabel#connectionBadge {{ border-radius: {d.RADIUS_MEDIUM}px; padding: {d.BADGE_PADDING};
    font-weight: {d.WEIGHT_BOLD}; }}
QLabel#connectionBadge[state="online"] {{ background: {c.success_bg}; color: {c.success}; }}
QLabel#connectionBadge[state="offline"] {{ background: {c.danger_bg}; color: {c.danger}; }}
QLabel#connectionBadge[state="checking"] {{ background: {c.surface_alt}; color: {c.muted}; }}

QMenuBar {{ background: {c.surface}; border-bottom: 1px solid {c.border}; }}
QMenuBar::item {{ padding: {d.MENU_BAR_ITEM_PADDING}; background: transparent; }}
QMenuBar::item:selected {{ background: {c.surface_alt}; border-radius: {d.RADIUS_TINY}px; }}
QMenu {{ background: {c.surface}; border: 1px solid {c.border}; padding: {d.LIST_PADDING}; }}
QMenu::item {{ padding: {d.MENU_ITEM_PADDING}; border-radius: {d.RADIUS_TINY}px; }}
QMenu::item:selected {{ background: {c.accent_soft}; color: {c.text}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
"""
