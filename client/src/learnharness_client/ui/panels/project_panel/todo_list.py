"""Adding, editing, moving and removing to-dos."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem

from learnharness_client.domain.project_plan import MAX_TODOS, clean_todo

from ....texts import T


class PanelTodoList:
    """The child's to-do list."""

    def _add_own_todo(self) -> None:
        text = clean_todo(self.new_todo.text())
        if not text:
            return
        if self.plan.has_todo(text):
            self._set_message(T.PLAN_ALREADY_LISTED, "neutral")
            return
        if not self.plan.add_todo(text):
            self._set_message(T.PLAN_LIST_FULL.format(count=MAX_TODOS), "error")
            return
        self.new_todo.clear()
        self._set_message("", "neutral")
        self._changed()
        self.todos.setCurrentRow(self.todos.count() - 1)

    def _item_changed(self, item: QListWidgetItem) -> None:
        row = self.todos.row(item)
        if not 0 <= row < len(self.plan.todos):
            return
        todo = self.plan.todos[row]
        text = clean_todo(item.text())
        if text and not self.plan.has_todo(text, ignore=todo):
            todo.text = text
        todo.done = item.checkState() == Qt.CheckState.Checked
        self.todos.blockSignals(True)
        self._style_item(item, todo)
        self.todos.blockSignals(False)
        self._mark_current()
        self._render_progress()
        self._sync_buttons()
        self._save()

    def _work_on_selected(self) -> None:
        row = self.todos.currentRow()
        if 0 <= row < len(self.plan.todos) and not self.plan.todos[row].done:
            self.plan.select_todo(self.plan.todos[row])
            self._changed()
            self.todos.setCurrentRow(row)

    def complete_current(self) -> None:
        if self.plan.complete_current() is not None:
            self._changed()

    def _move_current(self, step: int) -> None:
        row = self.todos.currentRow()
        target = row + step
        if row < 0 or not 0 <= target < len(self.plan.todos):
            return
        todos = self.plan.todos
        todos[row], todos[target] = todos[target], todos[row]
        self._changed()
        self.todos.setCurrentRow(target)

    def _remove_current(self) -> None:
        row = self.todos.currentRow()
        if not 0 <= row < len(self.plan.todos):
            return
        del self.plan.todos[row]
        self._changed()
        self.todos.setCurrentRow(min(row, self.todos.count() - 1))
