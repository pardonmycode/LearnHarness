"""Rounded card used by several panels."""

from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout

from learnharness_client import design


def card(title: str) -> tuple[QFrame, QVBoxLayout]:
    """Rounded surface with a small section title."""
    frame = QFrame()
    frame.setProperty("card", "true")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(*design.CARD_MARGINS)
    layout.setSpacing(design.CARD_SPACING)
    label = QLabel(title)
    label.setProperty("role", "section")
    layout.addWidget(label)
    return frame, layout
