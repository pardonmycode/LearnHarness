"""Keyboard-accessible ordering exercise."""

from __future__ import annotations

from learnharness_protocol import OrderingExercise, Submission
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QAbstractItemView, QListWidget, QListWidgetItem

from .base import ExerciseWidget


class OrderList(QListWidget):
    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 - Qt API
        if event.modifiers() & Qt.KeyboardModifier.AltModifier and event.key() in (
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
        ):
            row = self.currentRow()
            target = row - 1 if event.key() == Qt.Key.Key_Up else row + 1
            if 0 <= row < self.count() and 0 <= target < self.count():
                item = self.takeItem(row)
                self.insertItem(target, item)
                self.setCurrentRow(target)
            return
        super().keyPressEvent(event)


class OrderingWidget(ExerciseWidget):
    def __init__(self, exercise: OrderingExercise, parent=None) -> None:
        super().__init__(exercise, parent)
        self.items = OrderList()
        self.items.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.items.setAccessibleName("Elemente in die richtige Reihenfolge bringen")
        for item in exercise.items:
            widget_item = QListWidgetItem(item.text)
            widget_item.setData(Qt.ItemDataRole.UserRole, item.id)
            self.items.addItem(widget_item)
        self.layout.addWidget(self.items)
        self.finish_layout()

    def answers(self) -> Submission:
        order = [
            str(self.items.item(row).data(Qt.ItemDataRole.UserRole))
            for row in range(self.items.count())
        ]
        return Submission(exercise_id=self.exercise.id, answers={"order": order})
