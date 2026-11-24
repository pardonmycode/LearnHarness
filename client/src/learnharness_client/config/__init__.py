"""Application settings and writable application-data locations."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QStandardPaths

from .admin_settings import AdminSettings
from .base import SettingsBase, data_dir_override
from .plans import PlanSettings
from .preferences import PreferenceSettings
from .profiles import ProfileSettings
from .teacher import TeacherSettings

__all__ = ["AppSettings", "app_data_dir"]


class AppSettings(
    PreferenceSettings, AdminSettings, PlanSettings, TeacherSettings, ProfileSettings, SettingsBase
):
    """All settings of the app; each group lives in its own file."""


def app_data_dir() -> Path:
    override = data_dir_override()
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    path = override / "data" if override is not None else Path(location)
    path.mkdir(parents=True, exist_ok=True)
    return path
