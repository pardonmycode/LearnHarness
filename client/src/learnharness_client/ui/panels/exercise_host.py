"""Shared helper: a place in a panel that shows one exercise at a time."""

from __future__ import annotations

from learnharness_protocol import ReviewResult
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from ..exercises.base import ExerciseWidget
from ..exercises.factory import create_exercise_widget


class ExerciseHost(QObject):
    submitted = pyqtSignal(object)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.widget = QWidget(parent)
        self._layout = QVBoxLayout(self.widget)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.current: QWidget | None = None

    def show(self, exercise) -> QWidget:
        self.clear()
        widget = create_exercise_widget(exercise, self.widget)
        self.current = widget
        self._layout.addWidget(widget)
        if isinstance(widget, ExerciseWidget):
            widget.submitted.connect(self.submitted)
        return widget

    def show_result(self, review: ReviewResult) -> None:
        if isinstance(self.current, ExerciseWidget):
            self.current.show_result(review)

    def submission_failed(self) -> None:
        if isinstance(self.current, ExerciseWidget):
            self.current.submission_failed()

    def clear(self) -> None:
        if self.current is not None:
            self._layout.removeWidget(self.current)
            self.current.deleteLater()
            self.current = None
