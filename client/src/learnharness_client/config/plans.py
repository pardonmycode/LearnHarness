"""Missions and project plans per profile."""

from __future__ import annotations

import json

from .base import SettingsBase


class PlanSettings(SettingsBase):
    """Missions and plans."""

    def mission_progress(self, profile_id: str) -> dict[str, object]:
        """Last mission (as JSON-ready dict) plus the ids of the finished steps."""
        value = self._json_value(f"missions/{profile_id}/current", {})
        return value if isinstance(value, dict) else {}

    def save_mission_progress(self, profile_id: str, data: dict[str, object]) -> None:
        self._settings.setValue(
            f"missions/{profile_id}/current", json.dumps(data, ensure_ascii=False)
        )

    def project_plan(self, profile_id: str, project_id: str) -> dict[str, object]:
        value = self._json_value(f"project_plans/{profile_id}/{project_id}", {})
        return value if isinstance(value, dict) else {}

    def save_project_plan(self, profile_id: str, project_id: str, data: dict[str, object]) -> None:
        self._settings.setValue(
            f"project_plans/{profile_id}/{project_id}", json.dumps(data, ensure_ascii=False)
        )

    def assigned_missions(self, profile_id: str) -> dict[str, object]:
        """Last mission list from the administration (JSON-ready), kept for offline use."""
        value = self._json_value(f"missions/{profile_id}/assigned", {})
        return value if isinstance(value, dict) else {}

    def save_assigned_missions(self, profile_id: str, data: dict[str, object]) -> None:
        self._settings.setValue(
            f"missions/{profile_id}/assigned", json.dumps(data, ensure_ascii=False)
        )

    @property
    def pending_mission_reports(self) -> set[tuple[str, str]]:
        """Finished missions (profile id, mission id) not yet reported to the administration."""
        value = self._json_value("admin/pending_missions", [])
        if not isinstance(value, list):
            return set()
        return {
            (str(item[0]), str(item[1]))
            for item in value
            if isinstance(item, list) and len(item) == 2
        }

    def _set_pending_mission_reports(self, reports: set[tuple[str, str]]) -> None:
        self._settings.setValue(
            "admin/pending_missions", json.dumps(sorted(list(item) for item in reports))
        )

    def add_pending_mission_report(self, profile_id: str, mission_id: str) -> None:
        self._set_pending_mission_reports(self.pending_mission_reports | {(profile_id, mission_id)})

    def clear_pending_mission_report(self, profile_id: str, mission_id: str) -> None:
        self._set_pending_mission_reports(self.pending_mission_reports - {(profile_id, mission_id)})
