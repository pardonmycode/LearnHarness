"""Password-protected teacher area for local profiles and LearnAgent levels."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import StudentProfile

from ...texts import T
from ..theme import set_state

MIN_PASSWORD_LENGTH = 6


class PasswordDialog(QDialog):
    """Sets a new password (``create=True``) or asks for the existing one."""

    def __init__(self, settings: AppSettings, *, create: bool, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.create = create
        self.setWindowTitle(T.TEACHER_TITLE)
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        if create:
            intro = QLabel(T.TEACHER_SET_PASSWORD_INTRO)
            intro.setWordWrap(True)
            intro.setProperty("role", "muted")
            layout.addWidget(intro)
        form = QFormLayout()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setAccessibleName(T.TEACHER_PASSWORD_A11Y)
        form.addRow(T.TEACHER_PASSWORD, self.password)
        self.repeat = QLineEdit()
        self.repeat.setEchoMode(QLineEdit.EchoMode.Password)
        self.repeat.setAccessibleName(T.TEACHER_PASSWORD_REPEAT)
        if create:
            form.addRow(T.TEACHER_PASSWORD_REPEAT, self.repeat)
        layout.addLayout(form)
        self.error = QLabel()
        self.error.setWordWrap(True)
        self.error.hide()
        layout.addWidget(self.error)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok = buttons.button(QDialogButtonBox.StandardButton.Ok)
        assert ok is not None
        ok.setText(T.TEACHER_UNLOCK)
        ok.setProperty("primary", "true")
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _show_error(self, text: str) -> None:
        self.error.setText(text)
        self.error.show()
        set_state(self.error, callout="error")

    def _accept(self) -> None:
        password = self.password.text()
        if self.create:
            if len(password) < MIN_PASSWORD_LENGTH:
                self._show_error(T.TEACHER_PASSWORD_TOO_SHORT)
                return
            if password != self.repeat.text():
                self._show_error(T.TEACHER_PASSWORD_MISMATCH)
                return
            self.settings.set_teacher_password(password)
            self.accept()
            return
        if not self.settings.check_teacher_password(password):
            self.password.clear()
            self._show_error(T.TEACHER_PASSWORD_WRONG)
            return
        self.accept()


def unlock_teacher_area(settings: AppSettings, parent: QWidget | None = None) -> bool:
    """First use sets the password, later uses ask for it."""
    dialog = PasswordDialog(settings, create=not settings.has_teacher_password(), parent=parent)
    return dialog.exec() == QDialog.DialogCode.Accepted


class TeacherDialog(QDialog):
    """Only reachable after :func:`unlock_teacher_area` returned ``True``."""

    level_changed = pyqtSignal(str, int)  # profile_id, max unlocked level

    def __init__(self, settings: AppSettings, current_profile_id: str, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.current_profile_id = current_profile_id
        self.setWindowTitle(T.TEACHER_TITLE)
        self.resize(620, 440)
        layout = QVBoxLayout(self)
        heading = QLabel(T.TEACHER_TITLE)
        heading.setProperty("role", "heading")
        intro = QLabel(T.TEACHER_INTRO)
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")
        layout.addWidget(heading)
        layout.addWidget(intro)

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
        actions.addWidget(self.reset_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)
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
        enabled = profile is not None
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

    def _change_password(self) -> None:
        PasswordDialog(self.settings, create=True, parent=self).exec()
