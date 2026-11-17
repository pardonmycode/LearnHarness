"""Per-skill progress without scores or rankings."""

from __future__ import annotations

from learnharness_protocol import ProgressUpdate
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

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
        self.layout.addWidget(QLabel("Deine Fähigkeiten"))
        self.layout.addStretch(1)

    def set_progress(self, progress: ProgressUpdate) -> None:
        while self.layout.count() > 1:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for skill in progress.skills:
            level = int(skill.level)
            symbols = "●" * level + "○" * (3 - level)
            label = QLabel(f"{skill.label}: {symbols}  {LEVEL_WORDS[level]}")
            label.setAccessibleName(f"{skill.label}: {LEVEL_WORDS[level]}")
            self.layout.insertWidget(self.layout.count() - 1, label)
