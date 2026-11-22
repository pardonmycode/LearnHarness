"""Access to QSettings shared by all settings groups."""

from __future__ import annotations

import json

from PyQt6.QtCore import QSettings


class SettingsBase:
    """Holds the QSettings object."""

    def __init__(self) -> None:
        self._settings = QSettings("LearnHarness", "LearnHarnessClient")

    def _json_value(self, key: str, default: object) -> object:
        try:
            return json.loads(str(self._settings.value(key, json.dumps(default))))
        except json.JSONDecodeError:
            return default

    def value(self, key: str, default: object = None) -> object:
        return self._settings.value(key, default)

    def set_value(self, key: str, value: object) -> None:
        self._settings.setValue(key, value)
