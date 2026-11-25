"""Dialogs opened from the main window."""

from __future__ import annotations

from PyQt6.QtCore import QByteArray
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QMessageBox, QSplitter

from learnharness_client import design

from ...texts import T
from ..dialogs.backup_dialog import BackupDialog
from ..dialogs.changes_dialog import ChangesDialog
from ..dialogs.settings_dialog import SettingsDialog
from ..dialogs.teacher_dialog import TeacherDialog, unlock_teacher_area
from ..dialogs.tutorial_dialog import TutorialDialog
from ..panels.diagnostics_panel import DiagnosticsPanel


class WindowDialogs:
    """Settings, teacher area, versions, tutorial and the saved window layout."""

    def _restore_window_state(self) -> None:
        geometry = self.settings.value("window/geometry")
        state = self.settings.value("window/state")
        if isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)
        if isinstance(state, QByteArray):
            self.restoreState(state)
        for key, splitter in self._saved_splitters():
            sizes = self.settings.value(key)
            if isinstance(sizes, list) and len(sizes) == splitter.count():
                splitter.setSizes([int(size) for size in sizes])
            elif splitter is self.splitter:
                tabs = round(self.width() * design.LEARNING_TABS_SHARE)
                splitter.setSizes([self.width() - tabs, tabs])

    def _saved_splitters(self) -> tuple[tuple[str, QSplitter], ...]:
        return (
            ("window/main_splitter_v2", self.splitter),
            ("window/code_splitter", self.code_splitter),
            ("window/work_splitter", self.work_splitter),
            ("window/side_splitter", self.side_splitter),
        )

    def open_relative_file(self, relative: str) -> None:
        if self.project:
            self.editor_tabs.open_file(self.project.root / relative)

    def open_problem(self, relative: str, line: int) -> None:
        self.open_relative_file(relative)
        self.editor_tabs.goto_line(line)

    def show_diagnostics(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(T.DIAGNOSTICS)
        dialog.resize(*design.LOG_DIALOG_SIZE)
        layout = QHBoxLayout(dialog)
        panel = DiagnosticsPanel(self.server_url)
        panel.server.setText(self.diagnostics.server.text())
        panel.model.setText(self.diagnostics.model.text())
        panel.session.setText(self.diagnostics.session.text())
        panel.latency.setText(self.diagnostics.latency.text())
        panel.last_error.setText(self.diagnostics.last_error.text())
        layout.addWidget(panel)
        dialog.exec()

    def show_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            # Autosave and the changes view apply immediately; the rest after a restart.
            self.learn_agent_panel.changes_toggle.setChecked(self.settings.show_agent_changes)
            QMessageBox.information(self, T.SETTINGS_SAVED_TITLE, T.SETTINGS_SAVED)

    def _set_show_changes(self, enabled: bool) -> None:
        self.settings.show_agent_changes = enabled

    def _generated_file_applied(self, file_name: str, old: str, new: str) -> None:
        if self.settings.show_agent_changes and old != new:
            ChangesDialog(file_name, old, new, self).exec()

    def show_teacher_area(self) -> None:
        if not unlock_teacher_area(self.settings, self):
            return
        dialog = TeacherDialog(self.settings, self.student_profile.profile_id, self)
        dialog.level_changed.connect(self._teacher_level_changed)
        dialog.exec()

    def _teacher_level_changed(self, profile_id: str, level: int) -> None:
        if profile_id == self.student_profile.profile_id:
            self.learn_agent_panel.set_max_unlocked(level)

    def show_older_versions(self) -> None:
        document = self.editor_tabs.current_document()
        if document is None:
            QMessageBox.information(self, T.OLDER_VERSIONS, T.OPEN_FILE_FIRST)
            return
        backups = self.editor_tabs.backups_for_current()
        if not backups:
            QMessageBox.information(
                self, T.OLDER_VERSIONS, T.NO_BACKUPS.format(file=document.path.name)
            )
            return
        dialog = BackupDialog(document.path.name, backups, self)
        if (
            dialog.exec()
            and dialog.restored_text is not None
            and self.editor_tabs.restore_into_current(dialog.restored_text)
        ):
            self.statusBar().showMessage(T.VERSION_RESTORED.format(file=document.path.name), 8000)

    def show_tutorial(self) -> None:
        TutorialDialog(self).exec()
        self.settings.mark_tutorial_seen(self.student_profile.profile_id)

    def show_tutorial_once(self) -> None:
        if not self.settings.tutorial_seen(self.student_profile.profile_id):
            self.show_tutorial()
