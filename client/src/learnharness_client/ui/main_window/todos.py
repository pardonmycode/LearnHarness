"""Connects the project's to-do list with LearnAgent, missions and tutor."""

from __future__ import annotations

from ...texts import T


class TodoActions:
    """Every tab works on the to-do that is currently up."""

    def _current_todo_text(self) -> str | None:
        todo = self.project_panel.plan.current_todo()
        return todo.text if todo else None

    def _project_context(self) -> dict[str, object]:
        """What every request tells the helper about the project and its plan."""
        plan = self.project_panel.plan
        return {
            "project_description": plan.description.strip() or None,
            "project_todos": [item.text for item in plan.todos],
            "project_done_todos": [item.text for item in plan.todos if item.done],
            "active_todo": self._current_todo_text(),
        }

    def _sync_todo_bar(self) -> None:
        plan = self.project_panel.plan
        text = self._current_todo_text()
        if text != self.todo_bar.todo_text:
            self._todo_hint_level = 0
            self.tutor_panel.hint_progress.setValue(0)
        current = plan.current_todo()
        position = plan.todos.index(current) + 1 if current else 0
        self.todo_bar.show_todo(text, position, len(plan.todos))

    def _learn_current_todo(self) -> None:
        text = self._current_todo_text()
        if text is None:
            return
        self.learn_agent_panel.prompt.setPlainText(text)
        self.learning_tabs.setCurrentWidget(self.learn_agent_panel)
        self.learn_agent_panel.prompt.setFocus()

    def _mission_for_current_todo(self) -> None:
        text = self._current_todo_text()
        if text is None:
            return
        self.learning_tabs.setCurrentWidget(self.mission_panel)
        panel = self.mission_panel
        if panel.mission is not None and panel.next_step() is not None:
            # Never replace a mission the child is still working on.
            self.statusBar().showMessage(T.TODO_MISSION_RUNNING, 8000)
            return
        panel.reset()
        panel.request_mission(text)

    def _ask_tutor_about_todo(self) -> None:
        self.learning_tabs.setCurrentWidget(self.tutor_panel)
        self.tutor_panel.input.setFocus()

    def _next_hint(self) -> None:
        if self._current_todo_text() is None:
            self.tutor_client.request_next_hint(self.current_task_id)
            return
        self._todo_hint_level = min(4, self._todo_hint_level + 1)
        self._todo_hint_pending = True
        self.tutor_panel.ask(T.TODO_HINT_REQUEST.format(level=self._todo_hint_level))

    def _show_todo_hint_level(self) -> None:
        if self._todo_hint_pending:
            self._todo_hint_pending = False
            self.tutor_panel.hint_progress.setValue(self._todo_hint_level)

    def _finish_current_todo(self) -> None:
        self.project_panel.complete_current()
        self.todo_bar.question.hide()
        self.statusBar().showMessage(T.TODO_FINISHED, 6000)
