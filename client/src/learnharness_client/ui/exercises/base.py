"""Base class for exercises that never modify project files."""

from __future__ import annotations

from learnharness_protocol import ReviewResult, Submission
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class ExerciseWidget(QWidget):
    submitted = pyqtSignal(object)

    def __init__(self, exercise, parent=None) -> None:
        super().__init__(parent)
        self.exercise = exercise
        self.layout = QVBoxLayout(self)
        self.prompt = QLabel(exercise.prompt)
        self.prompt.setWordWrap(True)
        self.prompt.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.layout.addWidget(self.prompt)
        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        self.submit_button = QPushButton("Antwort prüfen")
        self.submit_button.setAccessibleName("Antwort prüfen")
        self.submit_button.clicked.connect(self._submit)

    def finish_layout(self) -> None:
        self.layout.addWidget(self.submit_button)
        self.layout.addWidget(self.result_label)
        self.layout.addStretch(1)

    def answers(self) -> Submission:
        raise NotImplementedError

    def _submit(self) -> None:
        self.submitted.emit(self.answers())

    def show_result(self, result: ReviewResult) -> None:
        symbol = "✓" if result.correct else "✗" if result.correct is False else "ℹ"
        self.result_label.setText(f"{symbol} {result.feedback}")
        self.result_label.setStyleSheet(
            "color: #15803d; font-weight: bold;"
            if result.correct
            else "color: #b91c1c; font-weight: bold;"
        )

    def reset(self) -> None:
        self.result_label.clear()
        self.submit_button.setEnabled(True)
