"""Connects the project description with the other tabs."""

from __future__ import annotations


class ProjectFlow:
    """Every tab knows what the child's project is about."""

    def _project_context(self) -> dict[str, object]:
        """What every request tells the helper about the project."""
        plan = self.project_panel.plan
        return {
            "project_description": plan.description.strip() or None,
            "project_done_missions": list(plan.finished_missions),
        }

    def _sync_project_idea(self) -> None:
        self.mission_panel.set_project_idea(bool(self.project_panel.plan.description.strip()))

    def _start_building(self) -> None:
        self.learning_tabs.setCurrentWidget(self.mission_panel)

    def _open_tutor(self) -> None:
        self.learning_tabs.setCurrentWidget(self.tutor_panel)
        self.tutor_panel.input.setFocus()

    def _next_hint(self) -> None:
        self.tutor_client.request_next_hint(self.current_task_id)
