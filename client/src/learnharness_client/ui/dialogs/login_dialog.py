"""Passwordless local profile login for different learning levels."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from learnharness_client import design
from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import (
    EXPERIENCE_LABELS,
    ExperienceLevel,
    StudentProfile,
)

from ...texts import T


class LoginDialog(QDialog):
    NEW_PROFILE = "__new__"

    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.selected_profile: StudentProfile | None = None
        self.profiles = {profile.profile_id: profile for profile in settings.student_profiles}
        self.setWindowTitle(T.LOGIN_TITLE)
        self.setMinimumWidth(design.LOGIN_MIN_WIDTH)

        layout = QVBoxLayout(self)
        heading = QLabel(T.LOGIN_HEADING)
        heading.setProperty("role", "heading")
        explanation = QLabel(T.LOGIN_INTRO)
        explanation.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(explanation)

        form = QFormLayout()
        self.profile_choice = QComboBox()
        self.profile_choice.setAccessibleName(T.LOGIN_PROFILE_A11Y)
        self.profile_choice.addItem(T.LOGIN_NEW_PROFILE, self.NEW_PROFILE)
        for profile in sorted(self.profiles.values(), key=lambda item: item.pseudonym.casefold()):
            self.profile_choice.addItem(profile.pseudonym, profile.profile_id)
        self.pseudonym = QLineEdit()
        self.pseudonym.setMaxLength(30)
        self.pseudonym.setPlaceholderText(T.LOGIN_PSEUDONYM_PLACEHOLDER)
        self.pseudonym.setAccessibleName(T.LOGIN_PSEUDONYM_A11Y)
        self.experience = QComboBox()
        self.experience.setAccessibleName(T.LOGIN_EXPERIENCE_A11Y)
        for level in ExperienceLevel:
            self.experience.addItem(EXPERIENCE_LABELS[level], int(level))
        form.addRow(T.LOGIN_PROFILE, self.profile_choice)
        form.addRow(T.LOGIN_PSEUDONYM, self.pseudonym)
        form.addRow(T.LOGIN_EXPERIENCE, self.experience)
        layout.addLayout(form)

        privacy = QLabel(T.LOGIN_PRIVACY)
        privacy.setWordWrap(True)
        privacy.setProperty("role", "muted")
        layout.addWidget(privacy)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(T.LOGIN_BUTTON)
        buttons.accepted.connect(self._login)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.profile_choice.currentIndexChanged.connect(self._profile_changed)
        self._select_last_profile()
        self._profile_changed()

    def _select_last_profile(self) -> None:
        if not self.settings.last_profile_id:
            return
        index = self.profile_choice.findData(self.settings.last_profile_id)
        if index >= 0:
            self.profile_choice.setCurrentIndex(index)

    def _profile_changed(self) -> None:
        profile_id = str(self.profile_choice.currentData())
        profile = self.profiles.get(profile_id)
        if profile is None:
            self.pseudonym.clear()
            self.experience.setCurrentIndex(0)
            self.pseudonym.setFocus()
            return
        self.pseudonym.setText(profile.pseudonym)
        self.experience.setCurrentIndex(int(profile.experience_level))

    def _login(self) -> None:
        try:
            profile_id = str(self.profile_choice.currentData())
            existing = self.profiles.get(profile_id)
            if existing is None:
                profile = StudentProfile.create(
                    self.pseudonym.text(), int(self.experience.currentData())
                )
            else:
                profile = existing.updated(
                    self.pseudonym.text(), int(self.experience.currentData())
                )
        except ValueError as exc:
            QMessageBox.warning(self, T.LOGIN_INCOMPLETE, str(exc))
            return
        self.settings.save_student_profile(profile)
        self.selected_profile = profile
        self.accept()
