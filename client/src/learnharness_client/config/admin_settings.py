"""Connection to the central administration."""

from __future__ import annotations

import json

from .base import SettingsBase


class AdminSettings(SettingsBase):
    """Central administration."""

    @property
    def admin_url(self) -> str:
        """Base URL of the central administration; empty means purely local profiles."""
        return str(self._settings.value("admin/url", "")).rstrip("/")

    @admin_url.setter
    def admin_url(self, value: str) -> None:
        self._settings.setValue("admin/url", value.strip().rstrip("/"))

    @property
    def admin_token(self) -> str:
        return str(self._settings.value("admin/token", ""))

    @admin_token.setter
    def admin_token(self, value: str) -> None:
        self._settings.setValue("admin/token", value.strip())

    @property
    def admin_group(self) -> str:
        """Optional group (e.g. "AG Montag") so a PC only lists the children of its group."""
        return str(self._settings.value("admin/group", ""))

    @admin_group.setter
    def admin_group(self, value: str) -> None:
        self._settings.setValue("admin/group", value.strip())

    @property
    def admin_enabled(self) -> bool:
        return bool(self.admin_url and self.admin_token)

    @property
    def synced_profile_ids(self) -> set[str]:
        value = self._json_value("admin/synced_ids", [])
        return {str(item) for item in value} if isinstance(value, list) else set()

    def set_synced_profile_ids(self, ids: set[str]) -> None:
        self._settings.setValue("admin/synced_ids", json.dumps(sorted(ids)))

    @property
    def pending_unlocks(self) -> dict[str, int]:
        """Level unlocks that could not reach the server yet (sent at the next sync)."""
        value = self._json_value("admin/pending_unlocks", {})
        if not isinstance(value, dict):
            return {}
        return {str(key): int(level) for key, level in value.items() if isinstance(level, int)}

    def add_pending_unlock(self, profile_id: str, level: int) -> None:
        pending = self.pending_unlocks
        pending[profile_id] = max(level, pending.get(profile_id, 0))
        self._settings.setValue("admin/pending_unlocks", json.dumps(pending))

    def clear_pending_unlock(self, profile_id: str) -> None:
        pending = self.pending_unlocks
        if pending.pop(profile_id, None) is not None:
            self._settings.setValue("admin/pending_unlocks", json.dumps(pending))
