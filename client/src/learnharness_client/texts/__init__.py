"""Central child-facing UI texts (German, simple sentences).

Every text a child can see lives here – windows, panels, dialogs, exercises and the
error messages raised by the domain and network layers – so a later ``QTranslator`` or a
second language only needs this one module. Placeholders use ``str.format`` names.
Exercise content itself comes from the learning server and is not translated here.
"""

from __future__ import annotations

from .app import AppTexts
from .editor import EditorTexts
from .errors import ErrorTexts
from .learning import LearningTexts
from .missions import MissionTexts
from .onboarding import OnboardingTexts
from .projects import ProjectTexts
from .settings import SettingsTexts
from .teacher import TeacherTexts
from .terminal import TerminalTexts
from .tools import ToolTexts

__all__ = ["T"]


class T(
    AppTexts,
    ToolTexts,
    OnboardingTexts,
    ErrorTexts,
    SettingsTexts,
    EditorTexts,
    LearningTexts,
    TeacherTexts,
    TerminalTexts,
    ProjectTexts,
    MissionTexts,
):
    """All child-facing texts; each group lives in its own file."""
