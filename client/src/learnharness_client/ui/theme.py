"""Accessible application palette and code colors."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

CODE_COLORS = {
    "keyword": QColor("#7c3aed"),
    "type": QColor("#0369a1"),
    "number": QColor("#b45309"),
    "string": QColor("#15803d"),
    "comment": QColor("#64748b"),
    "annotation": QColor("#be185d"),
    "node_path": QColor("#0f766e"),
}


def apply_theme(app: QApplication, font_size: int = 14, mode: str = "light") -> None:
    font = app.font()
    font.setPointSize(font_size)
    app.setFont(font)
    if mode == "high_contrast":
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#000000"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#000000"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#111111"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#ffdd00"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#000000"))
        app.setPalette(palette)


APP_STYLESHEET = """
QWidget { font-size: 14px; }
QPushButton { min-height: 30px; padding: 3px 10px; }
QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser, QComboBox { min-height: 28px; }
QTabBar::tab { padding: 7px 12px; }
QStatusBar { border-top: 1px solid palette(mid); }
QLabel#connectionOnline { color: #15803d; font-weight: bold; }
QLabel#connectionOffline { color: #b91c1c; font-weight: bold; }
"""
