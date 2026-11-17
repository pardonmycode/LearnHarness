"""Godot project folder selection."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget

from learnharness_client.domain.path_guard import PathNotAllowed
from learnharness_client.domain.project import GodotProject


def choose_project(parent: QWidget | None = None, start: str = "") -> GodotProject | None:
    directory = QFileDialog.getExistingDirectory(
        parent,
        "Godot-Projekt auswählen",
        start,
        QFileDialog.Option.ShowDirsOnly,
    )
    if not directory:
        return None
    try:
        return GodotProject.open(Path(directory))
    except (OSError, PathNotAllowed) as exc:
        QMessageBox.warning(parent, "Kein Godot-Projekt", str(exc))
        return None
