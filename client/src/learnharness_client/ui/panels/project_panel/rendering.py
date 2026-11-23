"""Drawing suggestions, the list and the buttons."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QListWidgetItem, QPushButton, QWidget

from learnharness_client.domain.project_plan import TodoItem, clean_todo

from ....texts import T
from ...theme import set_state


class PanelRendering:
    """Keeps the widgets in step with the plan."""

    def _changed(self) -> None:
        self._render_all()
        self._save()

    def _save(self) -> None:
        if self._has_project:
            self.plan_changed.emit(self.plan.to_dict())

    def _render_all(self) -> None:
        self._render_helper()
        self._render_todos()
        self._sync_buttons()

    def _render_helper(self) -> None:
        while self.suggestion_rows.count():
            entry = self.suggestion_rows.takeAt(0)
            widget = entry.widget() if entry else None
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        for text in self.plan.suggestions:
            self.suggestion_rows.addWidget(self._suggestion_row(text))
        self.question.setText(self.plan.question)
        self.question.setVisible(bool(self.plan.question))
        self.accept_all_button.setVisible(len(self.plan.suggestions) > 1)
        self.helper_card.setVisible(bool(self.plan.question or self.plan.suggestions))

    def _suggestion_row(self, text: str) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(text)
        label.setWordWrap(True)
        accept = QPushButton(T.PLAN_ACCEPT)
        accept.setAccessibleName(T.PLAN_ACCEPT_A11Y.format(todo=text))
        accept.clicked.connect(lambda _=False, value=text: self._accept(value))
        reject = QPushButton(T.PLAN_REJECT)
        reject.setAccessibleName(T.PLAN_REJECT_A11Y.format(todo=text))
        reject.clicked.connect(lambda _=False, value=text: self._reject(value))
        layout.addWidget(label, 1)
        layout.addWidget(accept)
        layout.addWidget(reject)
        return row

    def _render_todos(self) -> None:
        self.todos.blockSignals(True)
        self.todos.clear()
        for todo in self.plan.todos:
            item = QListWidgetItem(todo.text)
            item.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEditable
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            self._style_item(item, todo)
            self.todos.addItem(item)
        self.todos.blockSignals(False)
        self._mark_current()
        self._render_progress()

    def _mark_current(self) -> None:
        """The to-do that is up is bold, so the list and the bar above agree."""
        current = self.plan.current_todo()
        self.todos.blockSignals(True)
        for row, todo in enumerate(self.plan.todos):
            item = self.todos.item(row)
            if item is not None:
                font = item.font()
                font.setBold(todo is current)
                item.setFont(font)
        self.todos.blockSignals(False)

    @staticmethod
    def _style_item(item: QListWidgetItem, todo: TodoItem) -> None:
        item.setText(todo.text)
        item.setCheckState(Qt.CheckState.Checked if todo.done else Qt.CheckState.Unchecked)
        font = item.font()
        font.setStrikeOut(todo.done)
        item.setFont(font)

    def _render_progress(self) -> None:
        total = len(self.plan.todos)
        done = self.plan.done_count()
        text = T.PLAN_PROGRESS.format(done=done, total=total) if total else T.PLAN_EMPTY
        if total and done == total:
            text = T.PLAN_ALL_DONE
        self.progress_label.setText(text)
        self.progress.setRange(0, max(1, total))
        self.progress.setValue(done)
        self.progress.setAccessibleName(text)
        self.progress.setVisible(total > 0)

    def _sync_buttons(self) -> None:
        can_ask = self._online and not self._busy and bool(self.plan.description.strip())
        self.plan_button.setEnabled(can_ask)
        self.plan_button.setText(T.PLAN_AGAIN if self.plan.question else T.PLAN_START)
        self.reply_button.setEnabled(can_ask and bool(self.reply.text().strip()))
        self.add_button.setEnabled(bool(clean_todo(self.new_todo.text())))
        row = self.todos.currentRow()
        self.up_button.setEnabled(row > 0)
        self.down_button.setEnabled(0 <= row < self.todos.count() - 1)
        self.remove_button.setEnabled(row >= 0)
        selected = self.plan.todos[row] if 0 <= row < len(self.plan.todos) else None
        self.work_button.setEnabled(
            selected is not None and not selected.done and selected is not self.plan.current_todo()
        )

    def _set_message(self, text: str, state: str) -> None:
        self.message.setText(text)
        self.message.setVisible(bool(text))
        set_state(self.message, callout=state)
