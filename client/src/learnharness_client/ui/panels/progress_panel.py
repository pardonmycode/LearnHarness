"""Per-skill progress without scores or rankings."""

from __future__ import annotations

from learnharness_protocol import ProgressUpdate
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

LEVEL_WORDS = {
    0: "noch nicht begonnen",
    1: "mit Hilfe",
    2: "fast allein",
    3: "sicher",
}


class ProgressPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(10)
        heading = QLabel("Deine Fähigkeiten")
        heading.setProperty("role", "heading")
        intro = QLabel(
            "Hier siehst du, was du schon kannst. Es gibt keine Punkte und keine Rangliste."
        )
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")
        self.layout.addWidget(heading)
        self.layout.addWidget(intro)
        self._fixed_count = self.layout.count()
        self.layout.addStretch(1)

    def set_progress(self, progress: ProgressUpdate) -> None:
        while self.layout.count() > self._fixed_count + 1:
            item = self.layout.takeAt(self._fixed_count)
            if item is not None and item.widget():
                item.widget().deleteLater()
        for skill in progress.skills:
            level = int(skill.level)
            row = QFrame()
            row.setProperty("card", "true")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(14, 10, 14, 10)
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
