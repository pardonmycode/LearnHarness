"""Rounded card used by several panels."""

from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout


def card(title: str) -> tuple[QFrame, QVBoxLayout]:
    """Rounded surface with a small section title."""
    frame = QFrame()
    frame.setProperty("card", "true")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(8)
    label = QLabel(title)
    label.setProperty("role", "section")
    layout.addWidget(label)
    return frame, layout
