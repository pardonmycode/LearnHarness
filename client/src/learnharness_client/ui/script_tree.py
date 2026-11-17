"""Safe, compact GDScript tree built only from PathGuard-approved files."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem

from learnharness_client.domain.project import GodotProject


class ScriptTree(QTreeWidget):
    file_open_requested = pyqtSignal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.project: GodotProject | None = None
        self.setHeaderLabel("Skripte")
        self.setIndentation(14)
        self.setAnimated(True)
        self.itemDoubleClicked.connect(self._open_item)
        self.setAccessibleName("Skriptdateien im Godot-Projekt")

    def set_project(self, project: GodotProject) -> None:
        self.project = project
        self.refresh()

    def refresh(self) -> None:
        self.clear()
        if not self.project:
            return
        folders: dict[tuple[str, ...], QTreeWidgetItem] = {}
        for path in self.project.guard.iter_scripts():
            relative = path.relative_to(self.project.root)
            parent = self.invisibleRootItem()
            prefix: list[str] = []
            for folder_name in relative.parts[:-1]:
                prefix.append(folder_name)
                key = tuple(prefix)
                if key not in folders:
                    item = QTreeWidgetItem([folder_name])
                    item.setData(0, Qt.ItemDataRole.UserRole, None)
                    parent.addChild(item)
                    folders[key] = item
                parent = folders[key]
            file_item = QTreeWidgetItem([relative.name])
            file_item.setData(0, Qt.ItemDataRole.UserRole, str(path))
            parent.addChild(file_item)
        self.expandAll()

    def _open_item(self, item: QTreeWidgetItem) -> None:
        value = item.data(0, Qt.ItemDataRole.UserRole)
        if value:
            self.file_open_requested.emit(Path(str(value)))
