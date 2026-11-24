"""Connects the project description with the other tabs."""

from __future__ import annotations

from learnharness_client.domain.run_error import hide_private_paths

from ...texts import T


class ProjectFlow:
    """Every tab knows what the child's project is about."""

    def _project_context(self) -> dict[str, object]:
        """What every request tells the helper about the project."""
        plan = self.project_panel.plan
        return {
            "project_description": plan.description.strip() or None,
            "project_done_missions": list(plan.finished_missions),
        }

    def _latest_error(self) -> str | None:
        """The newest error from the terminal or the problem list, without private paths."""
        text = self.terminal.last_error or self.problems_panel.last_error()
        return hide_private_paths(text, self.project.root) if text and self.project else None

    def _sync_project_idea(self) -> None:
        self.mission_panel.set_project_idea(bool(self.project_panel.plan.description.strip()))

    def _start_building(self) -> None:
        self.learning_tabs.setCurrentWidget(self.mission_panel)

    def _open_tutor(self) -> None:
        self.learning_tabs.setCurrentWidget(self.tutor_panel)
        self.tutor_panel.input.setFocus()

    def _next_hint(self) -> None:
        """In a project the hint is about the project, otherwise about the example task."""
        if not self.project_panel.plan.description.strip():
            self.tutor_client.request_next_hint(self.current_task_id)
            return
        if not self.session_id:
            self.tutor_panel.show_error(T.WAIT_FOR_SESSION)
            return
        if not self.tutor_panel.hint_button.isEnabled():
            return
        level = min(4, self._project_hint_level + 1)
        self._pending_hint = level
        self.tutor_panel.show_request(T.TUTOR_HINT_REQUEST.format(level=level))
        self.send_tutor_message(T.TUTOR_HINT_REQUEST.format(level=level), hint_level=level)

    def _hint_answered(self) -> None:
        if self._pending_hint is not None:
            self._project_hint_level, self._pending_hint = self._pending_hint, None

    def _reset_project_hints(self) -> None:
        self._project_hint_level = 0
        self._pending_hint = None
        self.tutor_panel.hint_progress.setValue(0)
