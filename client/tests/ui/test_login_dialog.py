from __future__ import annotations

from pytestqt.qtbot import QtBot

from learnharness_client.domain.profile import ExperienceLevel, StudentProfile
from learnharness_client.ui.dialogs.login_dialog import LoginDialog


class StubSettings:
    def __init__(self, profiles: list[StudentProfile] | None = None) -> None:
        self.student_profiles = profiles or []
        self.last_profile_id = self.student_profiles[0].profile_id if self.student_profiles else ""
        self.saved: StudentProfile | None = None

    def save_student_profile(self, profile: StudentProfile) -> None:
        self.saved = profile


def test_new_profile_login_saves_level(qtbot: QtBot) -> None:
    settings = StubSettings()
    dialog = LoginDialog(settings)  # type: ignore[arg-type]
    qtbot.addWidget(dialog)
    dialog.pseudonym.setText("CodeFuchs")
    dialog.experience.setCurrentIndex(int(ExperienceLevel.SOME_PROJECTS))
    dialog._login()
    assert dialog.selected_profile is not None
    assert dialog.selected_profile.pseudonym == "CodeFuchs"
    assert dialog.selected_profile.experience_level == ExperienceLevel.SOME_PROJECTS
    assert settings.saved == dialog.selected_profile


def test_last_profile_is_preselected(qtbot: QtBot) -> None:
    profile = StudentProfile.create("PixelProfi", ExperienceLevel.INDEPENDENT)
    dialog = LoginDialog(StubSettings([profile]))  # type: ignore[arg-type]
    qtbot.addWidget(dialog)
    assert dialog.profile_choice.currentData() == profile.profile_id
    assert dialog.pseudonym.text() == "PixelProfi"
