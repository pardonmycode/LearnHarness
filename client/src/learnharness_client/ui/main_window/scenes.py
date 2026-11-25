"""The Godot scene of the open script: shown, sent along and changed after a correct answer."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from learnharness_protocol import ReviewResult, SceneEdit
from PyQt6.QtCore import QIODeviceBase, QSaveFile
from PyQt6.QtWidgets import QMessageBox

from learnharness_client.godot.scene_context import (
    FoundScene,
    find_scene,
    input_actions,
    project_files,
    read_scene,
    scene_context,
)
from learnharness_client.godot.scene_edit import SceneEditError, apply_scene_changes

from ...texts import T

LOG = logging.getLogger(__name__)


@dataclass
class ScenePlan:
    """A checked scene change that is written once the code was written."""

    path: Path
    relative: str
    old_text: str
    new_text: str


class SceneActions:
    """Godot scenes next to the scripts."""

    def _find_open_scene(self) -> FoundScene | None:
        if not self.project or self.project.language != "gdscript":
            return None
        relative = self._relative_current_file()
        return find_scene(self.project.root, relative) if relative else None

    def _refresh_scene_view(self) -> None:
        godot = bool(self.project) and self.project.language == "gdscript"
        self.scene_view.setVisible(godot)
        if godot:
            self.scene_view.show_scene(self._find_open_scene())

    def _scene_request_context(self) -> dict[str, object]:
        """Scene and input map for a request; the scene is kept as the base of a change."""
        self._last_scene = None
        if not self.project or self.project.language != "gdscript":
            return {}
        found = self._find_open_scene()
        self._last_scene = found
        return {
            "scene": scene_context(found) if found else None,
            "input_actions": input_actions(self.project.root),
            "project_files": project_files(self.project.root),
        }

    def _keep_scene_base(self) -> None:
        """Only an exercise that may change the scene remembers the scene it was made for."""
        self._scene_base = self._last_scene

    def _show_scene_preview(self, edit: SceneEdit | None) -> None:
        if self.scene_view.isVisible():
            self.scene_view.show_preview(edit)

    def _plan_scene_edit(self, review: ReviewResult) -> ScenePlan | None | bool:
        """None: nothing to change. False: the change does not fit, so no file is written."""
        if not review.scene_edits:
            return None
        edit = review.scene_edits[0]
        base: FoundScene | None = self._scene_base
        if self.project is None or base is None or base.relative != edit.path:
            LOG.warning("Rejected a scene edit for a scene that was not sent")
            self._scene_problem(T.SCENE_DOES_NOT_FIT.format(file=edit.path))
            return False
        current = read_scene(self.project.root, edit.path)
        if current is None or current.text != base.text:
            self._scene_problem(T.SCENE_CHANGED_MEANWHILE.format(file=edit.path))
            return False
        try:
            new_text = apply_scene_changes(current.text, list(edit.changes))
        except SceneEditError as exc:
            LOG.warning("Scene edit did not fit: %s", exc)
            self._scene_problem(T.SCENE_DOES_NOT_FIT.format(file=edit.path))
            return False
        return ScenePlan(current.path, edit.path, current.text, new_text)

    def _write_scene(self, plan: ScenePlan) -> bool:
        """With a backup in the older versions, written in one go."""
        try:
            disk = plan.path.read_text(encoding="utf-8")
            if disk != plan.old_text:
                self._scene_problem(T.SCENE_CHANGED_MEANWHILE.format(file=plan.relative))
                return False
            store = self.editor_tabs.store
            if store is not None:
                store.backup_manager.create(Path(plan.relative), disk.encode("utf-8"))
            data = plan.new_text.encode("utf-8")
            save_file = QSaveFile(str(plan.path))
            if not save_file.open(QIODeviceBase.OpenModeFlag.WriteOnly):
                raise OSError(T.FILE_OPEN_FAILED)
            if save_file.write(data) != len(data):
                save_file.cancelWriting()
                raise OSError(T.FILE_WRITE_INCOMPLETE)
            if not save_file.commit():
                raise OSError(T.FILE_COMMIT_FAILED)
        except (OSError, UnicodeDecodeError) as exc:
            self._scene_problem(T.SCENE_WRITE_FAILED.format(file=plan.relative, error=exc))
            return False
        self._scene_base = None
        self.statusBar().showMessage(T.SCENE_WRITTEN.format(file=plan.relative))
        self._refresh_scene_view()
        return True

    def _scene_problem(self, text: str) -> None:
        self._scene_base = None
        self.scene_view.show_preview(None)
        QMessageBox.warning(self, T.SCENE_NOT_WRITTEN_TITLE, text)
