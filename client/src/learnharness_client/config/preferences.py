"""Editor, server and display preferences."""

from __future__ import annotations

from pathlib import Path

from learnharness_client import design

from .base import SettingsBase


class PreferenceSettings(SettingsBase):
    """Preferences."""

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
        return int(self._settings.value("appearance/font_size", design.FONT_SIZE))

    @font_size.setter
    def font_size(self, value: int) -> None:
        self._settings.setValue(
            "appearance/font_size", max(design.FONT_SIZE_MIN, min(design.FONT_SIZE_MAX, value))
        )

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
