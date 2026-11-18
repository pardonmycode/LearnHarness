"""Godot project selection: known projects first, folder dialog as fallback."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget

from learnharness_client.domain.path_guard import PathNotAllowed
from learnharness_client.domain.project import GodotProject
from learnharness_client.godot.project_list import known_godot_projects

from ..texts import T
from .dialogs.project_choice_dialog import ProjectChoiceDialog


def choose_project_folder(parent: QWidget | None = None, start: str = "") -> GodotProject | None:
    directory = QFileDialog.getExistingDirectory(
        parent,
        T.CHOOSE_PROJECT,
        start,
        QFileDialog.Option.ShowDirsOnly,
    )
    if not directory:
        return None
    try:
        return GodotProject.open(Path(directory))
    except (OSError, PathNotAllowed) as exc:
        QMessageBox.warning(parent, T.NOT_A_PROJECT_TITLE, str(exc))
        return None


def choose_project(
    parent: QWidget | None = None,
    start: str = "",
    *,
    recent: list[str] | None = None,
    known: list[Path] | None = None,
) -> GodotProject | None:
    """Offer recent and Godot-known projects; without any, go straight to the folder dialog."""
    known = known_godot_projects() if known is None else known
    dialog = ProjectChoiceDialog(known, recent or [], parent)
    if dialog.project_count() == 0:
        dialog.deleteLater()
        return choose_project_folder(parent, start)
    if dialog.exec() and dialog.selected is not None:
        return dialog.selected
    if dialog.wants_folder_dialog:
        return choose_project_folder(parent, start)
    return None
