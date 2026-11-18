"""Application settings and writable application-data locations."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from pathlib import Path

from PyQt6.QtCore import QSettings, QStandardPaths

from learnharness_client.domain.profile import StudentProfile

_PBKDF2_ITERATIONS = 200_000


def _hash_password(password: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


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
    def godot_path(self) -> str:
        return str(self._settings.value("godot/executable", ""))

    @godot_path.setter
    def godot_path(self, value: str) -> None:
        self._settings.setValue("godot/executable", value.strip())

    @property
    def first_start_done(self) -> bool:
        return bool(self._settings.value("setup/first_start_done", False, type=bool))

    @first_start_done.setter
    def first_start_done(self, value: bool) -> None:
        self._settings.setValue("setup/first_start_done", value)

    @property
    def autosave(self) -> bool:
        """Save automatically shortly after typing (for younger children)."""
        return bool(self._settings.value("editor/autosave", False, type=bool))

    @autosave.setter
    def autosave(self, value: bool) -> None:
        self._settings.setValue("editor/autosave", value)

    @property
    def show_agent_changes(self) -> bool:
        """Show old and new code side by side after the LearnAgent wrote a file."""
        return bool(self._settings.value("learning/show_agent_changes", True, type=bool))

    @show_agent_changes.setter
    def show_agent_changes(self, value: bool) -> None:
        self._settings.setValue("learning/show_agent_changes", value)

    # Teacher area -------------------------------------------------------------

    def has_teacher_password(self) -> bool:
        return bool(self._settings.value("teacher/password", ""))

    def set_teacher_password(self, password: str) -> None:
        salt = secrets.token_bytes(16)
        digest = _hash_password(password, salt, _PBKDF2_ITERATIONS)
        self._settings.setValue(
            "teacher/password", f"{_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"
        )

    def check_teacher_password(self, password: str) -> bool:
        stored = str(self._settings.value("teacher/password", ""))
        try:
            iterations_text, salt_hex, digest_hex = stored.split("$")
            expected = bytes.fromhex(digest_hex)
            actual = _hash_password(password, bytes.fromhex(salt_hex), int(iterations_text))
        except ValueError:
            return False
        return hmac.compare_digest(actual, expected)

    def set_learning_level(self, profile_id: str, level: int) -> int:
        """Teacher override: may also lower the unlocked level."""
        value = max(1, min(10, level))
        self._settings.setValue(f"learning/{profile_id}/max_level", value)
        return value

    def reset_learning(self, profile_id: str) -> None:
        for group in ("learning", "progress", "tutorial"):
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
