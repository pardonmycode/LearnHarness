"""Learning profiles, levels and cached progress."""

from __future__ import annotations

import json

from learnharness_client.domain.profile import StudentProfile

from .base import SettingsBase


class ProfileSettings(SettingsBase):
    """Profiles and learning state."""

    def set_learning_level(self, profile_id: str, level: int) -> int:
        """Teacher override: may also lower the unlocked level."""
        value = max(1, min(10, level))
        self._settings.setValue(f"learning/{profile_id}/max_level", value)
        return value

    def reset_learning(self, profile_id: str) -> None:
        for group in ("learning", "progress", "tutorial", "missions"):
            self._settings.remove(f"{group}/{profile_id}")

    def delete_student_profile(self, profile_id: str) -> None:
        profiles = [item for item in self.student_profiles if item.profile_id != profile_id]
        self._settings.setValue(
            "profiles/items",
            json.dumps([item.to_dict() for item in profiles], ensure_ascii=False),
        )
        if self.last_profile_id == profile_id:
            self._settings.remove("profiles/last_id")
        self.reset_learning(profile_id)
        # Not part of reset_learning: a plan is the child's own work, not learning progress.
        self._settings.remove(f"project_plans/{profile_id}")

    def tutorial_seen(self, profile_id: str) -> bool:
        return bool(self._settings.value(f"tutorial/{profile_id}/seen", False, type=bool))

    def mark_tutorial_seen(self, profile_id: str) -> None:
        self._settings.setValue(f"tutorial/{profile_id}/seen", True)

    def cached_progress(self, profile_id: str) -> str | None:
        """Last ProgressUpdate JSON from the server, only for showing it offline."""
        value = self._settings.value(f"progress/{profile_id}/cache", "")
        return str(value) or None

    def cache_progress(self, profile_id: str, progress_json: str) -> None:
        self._settings.setValue(f"progress/{profile_id}/cache", progress_json)

    @property
    def student_profiles(self) -> list[StudentProfile]:
        raw = str(self._settings.value("profiles/items", "[]"))
        try:
            items = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if not isinstance(items, list):
            return []
        profiles: list[StudentProfile] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                profiles.append(StudentProfile.from_dict(item))
            except (KeyError, TypeError, ValueError):
                continue
        return profiles

    def save_student_profile(self, profile: StudentProfile, *, remember: bool = True) -> None:
        profiles = [
            existing
            for existing in self.student_profiles
            if existing.profile_id != profile.profile_id
        ]
        profiles.append(profile)
        profiles.sort(key=lambda item: item.pseudonym.casefold())
        self._settings.setValue(
            "profiles/items",
            json.dumps([item.to_dict() for item in profiles], ensure_ascii=False),
        )
        if remember:
            self._settings.setValue("profiles/last_id", profile.profile_id)

    def max_unlocked_learning_level(self, profile_id: str) -> int:
        value = int(self._settings.value(f"learning/{profile_id}/max_level", 1))
        return max(1, min(10, value))

    def unlock_learning_level(self, profile_id: str, level: int) -> int:
        unlocked = max(
            self.max_unlocked_learning_level(profile_id),
            max(1, min(10, level)),
        )
        self._settings.setValue(f"learning/{profile_id}/max_level", unlocked)
        return unlocked

    @property
    def last_profile_id(self) -> str:
        return str(self._settings.value("profiles/last_id", ""))
