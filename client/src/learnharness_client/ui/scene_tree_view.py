"""Read-only node tree of the scene the open script belongs to, with coming changes."""

from __future__ import annotations

from learnharness_protocol import (
    AddNode,
    ConnectSignal,
    DisconnectSignal,
    RemoveNode,
    SceneEdit,
    SetProperty,
)
from PyQt6.QtCore import QFileSystemWatcher, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem

from ..godot.scene_context import FoundScene
from ..texts import T
from .theme import colors


def _name(path: str) -> str:
    return path.rsplit("/", 1)[-1]


class SceneTreeView(QTreeWidget):
    """Shows what Godot's scene panel shows, so names in the code are easy to find."""

    scene_file_changed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.found: FoundScene | None = None
        self.preview: SceneEdit | None = None
        self._items: dict[str, QTreeWidgetItem] = {}
        self._signals: QTreeWidgetItem | None = None
        self.setHeaderLabel(T.SCENE_TREE)
        self.setIndentation(14)
        self.setAccessibleName(T.SCENE_TREE_A11Y)
        self.watcher = QFileSystemWatcher(self)
        self._reload = QTimer(self)
        self._reload.setSingleShot(True)
        self._reload.setInterval(300)
        self._reload.timeout.connect(self.scene_file_changed.emit)
        self.watcher.fileChanged.connect(lambda _path: self._reload.start())

    def show_scene(self, found: FoundScene | None) -> None:
        if self.found is None or found is None or self.found.relative != found.relative:
            self.preview = None  # a preview belongs to the scene it was made for
        self.found = found
        if self.watcher.files():
            self.watcher.removePaths(self.watcher.files())
        if found is not None:
            self.watcher.addPath(str(found.path))
        self._render()

    def show_preview(self, edit: SceneEdit | None) -> None:
        fits = edit is not None and self.found is not None and edit.path == self.found.relative
        self.preview = edit if fits else None
        self._render()

    def _render(self) -> None:
        self.clear()
        self._items = {}
        self._signals = None
        if self.found is None:
            self.setHeaderLabel(T.SCENE_TREE)
            self.addTopLevelItem(QTreeWidgetItem([T.SCENE_NONE]))
            return
        self.setHeaderLabel(T.SCENE_FILE.format(file=self.found.relative))
        for node in self.found.scene.nodes:
            kind = node.type or T.SCENE_INSTANCE.format(file=(node.instance or "?"))
            label = T.SCENE_NODE.format(name=_name(node.path), type=kind)
            if node.path == ".":
                label = T.SCENE_NODE.format(name=node.section.attr("name") or ".", type=kind)
            item = QTreeWidgetItem([label])
            item.setToolTip(0, node.path)
            if node.path == self.found.script_node:
                item.setText(0, label + T.SCENE_SCRIPT_MARK)
                font = QFont(item.font(0))
                font.setBold(True)
                item.setFont(0, font)
            self._attach(node.path, item)
        for section in self.found.scene.connections():
            text = T.SCENE_SIGNAL.format(
                signal=f"{section.attr('from')}.{section.attr('signal')}",
                method=section.attr("method") or "",
            )
            self._signal_group().addChild(QTreeWidgetItem([text]))
        if self.preview is not None:
            self._render_preview(self.preview)
        self.expandAll()

    def _attach(self, path: str, item: QTreeWidgetItem) -> None:
        parent_path = path.rsplit("/", 1)[0] if "/" in path else "."
        parent = self._items.get(parent_path) if path != "." else None
        if parent is None:
            self.addTopLevelItem(item)
        else:
            parent.addChild(item)
        self._items[path] = item

    def _signal_group(self) -> QTreeWidgetItem:
        if self._signals is None:
            self._signals = QTreeWidgetItem([T.SCENE_SIGNALS])
            self.addTopLevelItem(self._signals)
        return self._signals

    def _mark_new(self, item: QTreeWidgetItem) -> None:
        item.setForeground(0, QBrush(QColor(colors().success)))
        item.setToolTip(0, T.SCENE_PREVIEW_TIP)

    def _render_preview(self, edit: SceneEdit) -> None:
        for change in edit.changes:
            if isinstance(change, AddNode):
                path = change.name if change.parent == "." else f"{change.parent}/{change.name}"
                label = T.SCENE_NODE.format(name=change.name, type=change.type)
                item = QTreeWidgetItem([f"{label} · {T.SCENE_NEW}"])
                self._mark_new(item)
                self._attach(path, item)
            elif isinstance(change, SetProperty) and change.node in self._items:
                text = T.SCENE_CHANGED.format(property=change.property, value=change.value)
                item = QTreeWidgetItem([text])
                self._mark_new(item)
                self._items[change.node].addChild(item)
            elif isinstance(change, RemoveNode) and change.node in self._items:
                item = self._items[change.node]
                font = QFont(item.font(0))
                font.setStrikeOut(True)
                item.setFont(0, font)
                item.setText(0, f"{item.text(0)} · {T.SCENE_REMOVED}")
                item.setForeground(0, QBrush(QColor(colors().danger)))
            elif isinstance(change, ConnectSignal | DisconnectSignal):
                text = T.SCENE_SIGNAL.format(
                    signal=f"{change.from_node}.{change.signal}", method=change.method
                )
                new = isinstance(change, ConnectSignal)
                item = QTreeWidgetItem([f"{text} · {T.SCENE_NEW if new else T.SCENE_REMOVED}"])
                if new:
                    self._mark_new(item)
                else:
                    item.setForeground(0, QBrush(QColor(colors().danger)))
                self._signal_group().addChild(item)
