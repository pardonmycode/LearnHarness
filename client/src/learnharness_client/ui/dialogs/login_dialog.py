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

from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import (
    EXPERIENCE_LABELS,
    ExperienceLevel,
    StudentProfile,
)


class LoginDialog(QDialog):
    NEW_PROFILE = "__new__"

    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.selected_profile: StudentProfile | None = None
        self.profiles = {profile.profile_id: profile for profile in settings.student_profiles}
        self.setWindowTitle("Wer programmiert heute?")
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        heading = QLabel("Willkommen in der Godot-Programmierwerkstatt!")
        heading.setProperty("role", "heading")
        explanation = QLabel(
            "Wähle dein Profil oder lege ein neues an. Benutze bitte einen Spitznamen, "
            "nicht deinen vollständigen Namen. Die Erfahrungsstufe hilft dem Lernhelfer, "
            "passende Fragen und Hinweise zu geben."
        )
        explanation.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(explanation)

        form = QFormLayout()
        self.profile_choice = QComboBox()
        self.profile_choice.setAccessibleName("Gespeichertes Lernprofil")
        self.profile_choice.addItem("Neues Profil anlegen …", self.NEW_PROFILE)
        for profile in sorted(self.profiles.values(), key=lambda item: item.pseudonym.casefold()):
            self.profile_choice.addItem(profile.pseudonym, profile.profile_id)
        self.pseudonym = QLineEdit()
        self.pseudonym.setMaxLength(30)
        self.pseudonym.setPlaceholderText("Zum Beispiel: CodeFuchs")
        self.pseudonym.setAccessibleName("Spitzname")
        self.experience = QComboBox()
        self.experience.setAccessibleName("Erfahrung beim Programmieren")
        for level in ExperienceLevel:
            self.experience.addItem(EXPERIENCE_LABELS[level], int(level))
        form.addRow("Profil:", self.profile_choice)
        form.addRow("Spitzname:", self.pseudonym)
        form.addRow("Meine Erfahrung:", self.experience)
        layout.addLayout(form)

        privacy = QLabel(
            "Dieses Profil wird nur auf diesem Computer gespeichert. Es ist kein Passwort nötig."
        )
        privacy.setWordWrap(True)
        privacy.setProperty("role", "muted")
        layout.addWidget(privacy)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Anmelden")
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
            QMessageBox.warning(self, "Profil noch nicht vollständig", str(exc))
            return
        self.settings.save_student_profile(profile)
        self.selected_profile = profile
        self.accept()
