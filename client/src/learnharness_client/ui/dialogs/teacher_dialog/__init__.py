"""Password-protected teacher area for local profiles and LearnAgent levels."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from learnharness_client import design
from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import StudentProfile

from ....texts import T
from ..admin_dialog import AdminDialog
from .password import MIN_PASSWORD_LENGTH, PasswordDialog, unlock_teacher_area

__all__ = ["MIN_PASSWORD_LENGTH", "PasswordDialog", "TeacherDialog", "unlock_teacher_area"]


class TeacherDialog(QDialog):
    """Only reachable after :func:`unlock_teacher_area` returned ``True``."""

    level_changed = pyqtSignal(str, int)  # profile_id, max unlocked level

    def __init__(
        self, settings: AppSettings, current_profile_id: str, parent=None, *, server_url: str = ""
    ) -> None:
        super().__init__(parent)
        self.settings = settings
        self.server_url = server_url  # suggested as the administration's address
        self.current_profile_id = current_profile_id
        self.setWindowTitle(T.TEACHER_TITLE)
        self.resize(*design.TEACHER_DIALOG_SIZE)
        layout = QVBoxLayout(self)
        heading = QLabel(T.TEACHER_TITLE)
        heading.setProperty("role", "heading")
        intro = QLabel(T.TEACHER_INTRO)
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")
        layout.addWidget(heading)
        layout.addWidget(intro)
        self.central_notice = QLabel(T.TEACHER_CENTRAL_NOTICE)
        self.central_notice.setWordWrap(True)
        self.central_notice.setProperty("callout", "info")
        layout.addWidget(self.central_notice)

        self.profiles = QListWidget()
        self.profiles.setAccessibleName(T.TEACHER_PROFILES_A11Y)
        layout.addWidget(self.profiles, 1)
        self.empty = QLabel(T.TEACHER_NO_PROFILES)
        self.empty.setProperty("role", "muted")
        layout.addWidget(self.empty)

        level_row = QHBoxLayout()
        level_row.addWidget(QLabel(T.TEACHER_LEVEL))
        self.level = QSpinBox()
        self.level.setRange(1, 10)
        self.level.setAccessibleName(T.TEACHER_LEVEL_A11Y)
        self.apply_level = QPushButton(T.TEACHER_APPLY_LEVEL)
        self.apply_level.setProperty("primary", "true")
        level_row.addWidget(self.level)
        level_row.addWidget(self.apply_level)
        level_row.addStretch(1)
        layout.addLayout(level_row)

        actions = QHBoxLayout()
        self.reset_button = QPushButton(T.TEACHER_RESET)
        self.delete_button = QPushButton(T.TEACHER_DELETE)
        self.password_button = QPushButton(T.TEACHER_CHANGE_PASSWORD)
        self.admin_button = QPushButton(T.TEACHER_ADMIN)
        actions.addWidget(self.reset_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)
        actions.addWidget(self.admin_button)
        actions.addWidget(self.password_button)
        layout.addLayout(actions)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.profiles.currentItemChanged.connect(lambda *_: self._selection_changed())
        self.apply_level.clicked.connect(self._apply_level)
        self.reset_button.clicked.connect(self._reset)
        self.delete_button.clicked.connect(self._delete)
        self.password_button.clicked.connect(self._change_password)
        self.admin_button.clicked.connect(self._open_admin)
        self.refresh()

    def selected_profile(self) -> StudentProfile | None:
        item = self.profiles.currentItem()
        if item is None:
            return None
        profile_id = str(item.data(Qt.ItemDataRole.UserRole))
        for profile in self.settings.student_profiles:
            if profile.profile_id == profile_id:
                return profile
        return None

    def refresh(self, select_id: str | None = None) -> None:
        selected = select_id or (p.profile_id if (p := self.selected_profile()) else None)
        self.profiles.clear()
        for profile in self.settings.student_profiles:
            level = self.settings.max_unlocked_learning_level(profile.profile_id)
            text = T.TEACHER_PROFILE_ROW.format(
                pseudonym=profile.pseudonym, level=level, experience=profile.experience_label
            )
            if profile.profile_id == self.current_profile_id:
                text += T.TEACHER_CURRENT
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, profile.profile_id)
            self.profiles.addItem(item)
            if profile.profile_id == selected:
                self.profiles.setCurrentItem(item)
        if self.profiles.currentItem() is None and self.profiles.count():
            self.profiles.setCurrentRow(0)
        self.empty.setVisible(self.profiles.count() == 0)
        self._selection_changed()

    def _selection_changed(self) -> None:
        profile = self.selected_profile()
        central = self.settings.admin_enabled
        self.central_notice.setVisible(central)
        # With a central administration the server decides; local changes would be undone.
        enabled = profile is not None and not central
        for widget in (self.level, self.apply_level, self.reset_button, self.delete_button):
            widget.setEnabled(enabled)
        if profile is not None:
            self.level.setValue(self.settings.max_unlocked_learning_level(profile.profile_id))

    def _apply_level(self) -> None:
        profile = self.selected_profile()
        if profile is None:
            return
        level = self.settings.set_learning_level(profile.profile_id, self.level.value())
        self.level_changed.emit(profile.profile_id, level)
        self.refresh(profile.profile_id)

    def _confirm(self, text: str) -> bool:
        answer = QMessageBox.question(
            self,
            T.TEACHER_TITLE,
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _reset(self) -> None:
        profile = self.selected_profile()
        if profile is None:
            return
        if not self._confirm(T.TEACHER_RESET_CONFIRM.format(pseudonym=profile.pseudonym)):
            return
        self.settings.reset_learning(profile.profile_id)
        self.level_changed.emit(profile.profile_id, 1)
        self.refresh(profile.profile_id)

    def _delete(self) -> None:
        profile = self.selected_profile()
        if profile is None:
            return
        if profile.profile_id == self.current_profile_id:
            QMessageBox.information(self, T.TEACHER_TITLE, T.TEACHER_CANNOT_DELETE_CURRENT)
            return
        if not self._confirm(T.TEACHER_DELETE_CONFIRM.format(pseudonym=profile.pseudonym)):
            return
        self.settings.delete_student_profile(profile.profile_id)
        self.refresh()

    def _open_admin(self) -> None:
        AdminDialog(self.settings, self, suggested_url=self.server_url).exec()
        self.refresh()
        profile_id = self.current_profile_id
        self.level_changed.emit(profile_id, self.settings.max_unlocked_learning_level(profile_id))

    def _change_password(self) -> None:
        PasswordDialog(self.settings, create=True, parent=self).exec()
