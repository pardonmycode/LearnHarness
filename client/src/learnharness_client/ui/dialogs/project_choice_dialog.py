"""Pick a project from recent ones and those Godot already knows, or start a new one."""

from __future__ import annotations

import os
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from learnharness_client.domain.project import Project

from ...texts import T


class ProjectChoiceDialog(QDialog):
    """``selected`` is the chosen project; ``wants_folder_dialog`` asks for the fallback."""

    def __init__(self, known: list[Path], recent: list[str], parent=None) -> None:
        super().__init__(parent)
        self.selected: Project | None = None
        self.wants_folder_dialog = False
        self.wants_new_python = False
        self.setWindowTitle(T.PROJECT_CHOICE_TITLE)
        self.setMinimumSize(560, 400)

        layout = QVBoxLayout(self)
        heading = QLabel(T.PROJECT_CHOICE_TITLE)
        heading.setProperty("role", "heading")
        intro = QLabel(T.PROJECT_CHOICE_INTRO)
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")
        self.projects = QListWidget()
        self.projects.setAccessibleName(T.PROJECT_CHOICE_LIST_A11Y)
        layout.addWidget(heading)
        layout.addWidget(intro)
        layout.addWidget(self.projects, 1)

        seen: set[str] = set()
        entries = [(Path(item), T.PROJECT_CHOICE_RECENT_TAG) for item in recent]
        entries += [(path, T.PROJECT_CHOICE_GODOT_TAG) for path in known]
        for path, tag in entries:
            key = os.path.normcase(str(path))
            if key in seen:
                continue
            try:
                project = Project.open(path)
            except (OSError, ValueError):
                continue
            seen.add(os.path.normcase(str(project.root)))
            seen.add(key)
            item = QListWidgetItem(f"{project.name}\n{tag.format(path=project.root)}")
            item.setToolTip(str(project.root))
            item.setData(Qt.ItemDataRole.UserRole, project)
            self.projects.addItem(item)

        buttons = QHBoxLayout()
        other = QPushButton(T.PROJECT_CHOICE_OTHER_FOLDER)
        self.new_python_button = QPushButton(T.NEW_PYTHON_PROJECT)
        cancel = QPushButton(T.PROJECT_CHOICE_CANCEL)
        self.open_button = QPushButton(T.PROJECT_CHOICE_OPEN)
        self.open_button.setProperty("primary", "true")
        self.open_button.setDefault(True)
        buttons.addWidget(other)
        buttons.addWidget(self.new_python_button)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(self.open_button)
        layout.addLayout(buttons)

        other.clicked.connect(self._other_folder)
        self.new_python_button.clicked.connect(self._new_python)
        cancel.clicked.connect(self.reject)
        self.open_button.clicked.connect(self._open_current)
        self.projects.itemActivated.connect(lambda _item: self._open_current())
        self.projects.currentRowChanged.connect(lambda row: self.open_button.setEnabled(row >= 0))
        if self.projects.count():
            self.projects.setCurrentRow(0)
        else:
            self.open_button.setEnabled(False)

    def project_count(self) -> int:
        return self.projects.count()

    def _open_current(self) -> None:
        item = self.projects.currentItem()
        project = item.data(Qt.ItemDataRole.UserRole) if item else None
        if isinstance(project, Project):
            self.selected = project
            self.accept()

    def _new_python(self) -> None:
        self.wants_new_python = True
        self.reject()

    def _other_folder(self) -> None:
        self.wants_folder_dialog = True
        self.reject()
