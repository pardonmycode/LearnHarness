"""Application settings and writable application-data locations."""

from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtCore import QSettings, QStandardPaths

from learnharness_client.domain.profile import StudentProfile


class AppSettings:
    def __init__(self) -> None:
        self._settings = QSettings("LearnHarness", "LearnHarnessClient")

    @property
    def server_url(self) -> str:
        return str(self._settings.value("network/server_url", "http://learnserver:8765"))

    @server_url.setter
    def server_url(self, value: str) -> None:
        self._settings.setValue("network/server_url", value.rstrip("/"))

    @property
    def use_fake_server(self) -> bool:
        return bool(self._settings.value("network/fake", True, type=bool))

    @use_fake_server.setter
    def use_fake_server(self, value: bool) -> None:
        self._settings.setValue("network/fake", value)

    @property
    def font_size(self) -> int:
        return int(self._settings.value("appearance/font_size", 14))

    @font_size.setter
    def font_size(self, value: int) -> None:
        self._settings.setValue("appearance/font_size", max(11, min(28, value)))

    @property
    def theme(self) -> str:
        return str(self._settings.value("appearance/theme", "system"))

    @theme.setter
    def theme(self, value: str) -> None:
        self._settings.setValue("appearance/theme", value)

    @property
    def recent_projects(self) -> list[str]:
        value = self._settings.value("projects/recent", [])
        if isinstance(value, str):
            return [value]
        return [str(item) for item in value]

    def remember_project(self, path: Path) -> None:
        normalized = str(path.resolve())
        projects = [item for item in self.recent_projects if item != normalized]
        projects.insert(0, normalized)
        self._settings.setValue("projects/recent", projects[:5])

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

    def save_student_profile(self, profile: StudentProfile) -> None:
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

    def value(self, key: str, default: object = None) -> object:
        return self._settings.value(key, default)

    def set_value(self, key: str, value: object) -> None:
        self._settings.setValue(key, value)


def app_data_dir() -> Path:
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    path = Path(location)
    path.mkdir(parents=True, exist_ok=True)
    return path
