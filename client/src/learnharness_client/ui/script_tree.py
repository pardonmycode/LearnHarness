"""Safe, compact GDScript tree built only from PathGuard-approved files."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QFileSystemWatcher, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem

from learnharness_client.domain.project import GodotProject

from ..texts import T


def _is_junction(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction()) if callable(is_junction) else False


class ScriptTree(QTreeWidget):
    file_open_requested = pyqtSignal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.project: GodotProject | None = None
        self.setHeaderLabel(T.SCRIPTS)
        self.setIndentation(14)
        self.setAnimated(True)
        self.setAccessibleName(T.SCRIPTS_A11Y)
        self.itemActivated.connect(self._open_item)
        # New or deleted scripts (e.g. created in Godot) appear without a manual refresh.
        self.watcher = QFileSystemWatcher(self)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(400)
        self._refresh_timer.timeout.connect(self.refresh)
        self.watcher.directoryChanged.connect(lambda _path: self._refresh_timer.start())

    def set_project(self, project: GodotProject) -> None:
        self.project = project
        self.refresh()

    def refresh(self) -> None:
        self.clear()
        if self.watcher.directories():
            self.watcher.removePaths(self.watcher.directories())
        if not self.project:
            return
        self._watch_folders(self.project.root)
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

    def _watch_folders(self, root: Path, depth: int = 0) -> None:
        if depth > 6:
            return
        self.watcher.addPath(str(root))
        try:
            children = list(root.iterdir())
        except OSError:
            return
        for child in children:
            if child.name.startswith(".") or child.name == "addons":
                continue
            if child.is_dir() and not child.is_symlink() and not _is_junction(child):
                self._watch_folders(child, depth + 1)

    def _open_item(self, item: QTreeWidgetItem) -> None:
        value = item.data(0, Qt.ItemDataRole.UserRole)
        if value:
            self.file_open_requested.emit(Path(str(value)))
