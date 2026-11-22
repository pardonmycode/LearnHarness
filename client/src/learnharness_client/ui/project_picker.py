"""Project selection: known projects first, folder dialog as fallback, new Python projects."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QStandardPaths
from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QWidget

from learnharness_client.domain.path_guard import PathNotAllowed
from learnharness_client.domain.project import Project, create_python_project
from learnharness_client.godot.project_list import known_godot_projects

from ..texts import T
from .dialogs.project_choice_dialog import ProjectChoiceDialog


def choose_project_folder(parent: QWidget | None = None, start: str = "") -> Project | None:
    directory = QFileDialog.getExistingDirectory(
        parent,
        T.CHOOSE_PROJECT,
        start,
        QFileDialog.Option.ShowDirsOnly,
    )
    if not directory:
        return None
    try:
        return Project.open(Path(directory))
    except (OSError, PathNotAllowed) as exc:
        QMessageBox.warning(parent, T.NOT_A_PROJECT_TITLE, str(exc))
        return None


def new_python_project(parent: QWidget | None = None) -> Project | None:
    """Ask for a name and a place, then create the project folder there."""
    name, accepted = QInputDialog.getText(parent, T.NEW_PYTHON_PROJECT, T.NEW_PYTHON_PROJECT_PROMPT)
    if not accepted or not name.strip():
        return None
    start = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    directory = QFileDialog.getExistingDirectory(
        parent, T.NEW_PYTHON_PROJECT_WHERE, start, QFileDialog.Option.ShowDirsOnly
    )
    if not directory:
        return None
    try:
        return create_python_project(Path(directory), name)
    except (OSError, PathNotAllowed) as exc:
        QMessageBox.warning(parent, T.PROJECT_NOT_CREATED, str(exc))
        return None


def choose_python_script(
    parent: QWidget | None = None, start: str = ""
) -> tuple[Project, Path] | None:
    """Pick one .py file; its folder becomes the project."""
    file_name, _filter = QFileDialog.getOpenFileName(
        parent, T.OPEN_PYTHON_SCRIPT, start, T.PYTHON_FILE_FILTER
    )
    if not file_name:
        return None
    script = Path(file_name)
    try:
        project = Project.open(script.parent)
        if project.language != "python":
            raise PathNotAllowed(T.PYTHON_IN_GODOT_PROJECT)
        return project, project.guard.ensure_allowed(script)
    except (OSError, PathNotAllowed) as exc:
        QMessageBox.warning(parent, T.PROJECT_NOT_OPENED, str(exc))
        return None


def choose_project(
    parent: QWidget | None = None,
    start: str = "",
    *,
    recent: list[str] | None = None,
    known: list[Path] | None = None,
) -> Project | None:
    """Offer recent and Godot-known projects; without any, go straight to the folder dialog."""
    known = known_godot_projects() if known is None else known
    dialog = ProjectChoiceDialog(known, recent or [], parent)
    if dialog.project_count() == 0:
        dialog.deleteLater()
        return choose_project_folder(parent, start)
    if dialog.exec() and dialog.selected is not None:
        return dialog.selected
    if dialog.wants_new_python:
        return new_python_project(parent)
    if dialog.wants_folder_dialog:
        return choose_project_folder(parent, start)
    return None
