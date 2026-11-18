"""Small settings dialog; network changes apply after restart."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from learnharness_client.config import AppSettings
from learnharness_client.ui.theme import THEME_CHOICES

from ...texts import T


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle(T.SETTINGS_TITLE)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.server_url = QLineEdit(settings.server_url)
        self.fake_server = QCheckBox(T.SETTINGS_FAKE_SERVER)
        self.fake_server.setChecked(settings.use_fake_server)
        self.font_size = QSpinBox()
        self.font_size.setRange(11, 28)
        self.font_size.setValue(settings.font_size)
        self.theme = QComboBox()
        for value, label in THEME_CHOICES:
            self.theme.addItem(label, value)
        index = self.theme.findData(settings.theme)
        self.theme.setCurrentIndex(max(0, index))
        self.godot_path = QLineEdit(settings.godot_path)
        self.godot_path.setPlaceholderText(T.SETTINGS_GODOT_PLACEHOLDER)
        self.godot_path.setAccessibleName(T.SETTINGS_GODOT_A11Y)
        browse = QPushButton(T.SETTINGS_BROWSE)
        browse.clicked.connect(self._browse_godot)
        godot_row = QHBoxLayout()
        godot_row.addWidget(self.godot_path, 1)
        godot_row.addWidget(browse)
        self.server_url.setAccessibleName(T.SETTINGS_SERVER_A11Y)
        self.font_size.setAccessibleName(T.SETTINGS_FONT_SIZE_A11Y)
        self.theme.setAccessibleName(T.SETTINGS_THEME_A11Y)
        form.addRow(T.SETTINGS_SERVER, self.server_url)
        form.addRow(T.SETTINGS_GODOT, godot_row)
        form.addRow(T.SETTINGS_DEVELOPMENT, self.fake_server)
        self.autosave = QCheckBox(T.SETTINGS_AUTOSAVE)
        self.autosave.setChecked(settings.autosave)
        self.show_changes = QCheckBox(T.SETTINGS_SHOW_CHANGES)
        self.show_changes.setChecked(settings.show_agent_changes)
        form.addRow(T.SETTINGS_EDITOR, self.autosave)
        form.addRow(T.SETTINGS_LEARNING, self.show_changes)
        form.addRow(T.SETTINGS_FONT_SIZE, self.font_size)
        form.addRow(T.SETTINGS_THEME, self.theme)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self) -> None:
        url = self.server_url.text().strip()
        if url:
            self.settings.server_url = url
        self.settings.use_fake_server = self.fake_server.isChecked()
        self.settings.font_size = self.font_size.value()
        self.settings.theme = str(self.theme.currentData())
        self.settings.godot_path = self.godot_path.text()
        self.settings.autosave = self.autosave.isChecked()
        self.settings.show_agent_changes = self.show_changes.isChecked()
        self.accept()

    def _browse_godot(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(
            self, T.SETTINGS_CHOOSE_GODOT, self.godot_path.text(), T.SETTINGS_GODOT_FILTER
        )
        if path:
            self.godot_path.setText(path)
