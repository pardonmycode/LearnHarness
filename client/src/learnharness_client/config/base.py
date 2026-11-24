"""Access to QSettings shared by all settings groups."""

from __future__ import annotations

import json
import os
from pathlib import Path

from PyQt6.QtCore import QSettings

# The test stand keeps its profiles and settings apart from the real ones.
DATA_DIR_VARIABLE = "LEARNHARNESS_DATA_DIR"


def data_dir_override() -> Path | None:
    value = os.environ.get(DATA_DIR_VARIABLE, "").strip()
    return Path(value) if value else None


class SettingsBase:
    """Holds the QSettings object."""

    def __init__(self) -> None:
        override = data_dir_override()
        if override is not None:
            override.mkdir(parents=True, exist_ok=True)
            self._settings = QSettings(str(override / "settings.ini"), QSettings.Format.IniFormat)
        else:
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
