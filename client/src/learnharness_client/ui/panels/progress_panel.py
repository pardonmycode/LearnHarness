"""Per-skill progress without scores or rankings."""

from __future__ import annotations

from learnharness_protocol import ProgressUpdate
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from learnharness_client import design

from ...texts import T

LEVEL_WORDS = T.LEVEL_WORDS


class ProgressPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(*design.PANEL_MARGINS)
        self.layout.setSpacing(design.PANEL_SPACING_TIGHT)
        heading = QLabel(T.PROGRESS_HEADING)
        heading.setProperty("role", "heading")
        intro = QLabel(T.PROGRESS_INTRO)
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")
        self.offline_note = QLabel(T.PROGRESS_OFFLINE)
        self.offline_note.setProperty("role", "small")
        self.offline_note.hide()
        self.layout.addWidget(heading)
        self.layout.addWidget(intro)
        self.layout.addWidget(self.offline_note)
        self._fixed_count = self.layout.count()
        self.layout.addStretch(1)

    def set_progress(self, progress: ProgressUpdate, *, cached: bool = False) -> None:
        """``cached``: shown from the local copy while the server is unreachable."""
        self.offline_note.setVisible(cached)
        while self.layout.count() > self._fixed_count + 1:
            item = self.layout.takeAt(self._fixed_count)
            if item is not None and item.widget():
                item.widget().deleteLater()
        for skill in progress.skills:
            level = int(skill.level)
            row = QFrame()
            row.setProperty("card", "true")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(*design.PROGRESS_ROW_MARGINS)
            name = QLabel(skill.label)
            name.setProperty("role", "subheading")
            symbols = QLabel("●" * level + "○" * (3 - level))
            words = QLabel(LEVEL_WORDS[level])
            words.setProperty("role", "muted")
            row_layout.addWidget(name)
            row_layout.addStretch(1)
            row_layout.addWidget(words)
            row_layout.addWidget(symbols)
            row.setAccessibleName(f"{skill.label}: {LEVEL_WORDS[level]}")
            self.layout.insertWidget(self.layout.count() - 1, row)
