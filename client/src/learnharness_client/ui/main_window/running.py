"""Starting and stopping the project from the terminal."""

from __future__ import annotations

from pathlib import Path

from learnharness_client.domain.path_guard import PathNotAllowed
from learnharness_client.domain.run_target import RunNotPossible, run_target, script_to_run
from learnharness_client.godot.paths import find_godot_on_path

from ...texts import T


class RunActions:
    """Connects the terminal with the open project."""

    def _current_script(self) -> Path | None:
        document = self.editor_tabs.current_document()
        return document.path if document else None

    def run_script(self) -> None:
        if self.terminal.is_running():
            return
        if self.project is None:
            self.terminal.show_message(T.OPEN_PROJECT_FIRST)
            return
        godot = ""
        if self.project.language == "gdscript":
            godot = self.settings.godot_path or find_godot_on_path()
        try:
            target = run_target(self.project, self._current_script(), godot)
        except (RunNotPossible, PathNotAllowed) as exc:
            self.terminal.show_message(str(exc))
            return
        # Scripts import each other, so every open file must be on disk in its current state.
        for editor, document in list(self.editor_tabs.documents.items()):
            if document.dirty and not self.editor_tabs.save_editor(editor):
                return
        self.terminal.start(target)

    def stop_script(self) -> None:
        self.terminal.stop()

    def _update_run_target(self, _file: str = "") -> None:
        text, enabled = T.TERMINAL_START_EMPTY, False
        if self.project is not None and self.project.language == "gdscript":
            text, enabled = T.TERMINAL_START_GAME, True
        elif self.project is not None:
            try:
                script = script_to_run(self.project, self._current_script())
            except PathNotAllowed:
                script = None
            if script is not None:
                file = script.relative_to(self.project.root).as_posix()
                text, enabled = T.TERMINAL_START_SCRIPT.format(file=file), True
        self.terminal.set_start_label(text, enabled=enabled)
        self.run_action.setEnabled(enabled and not self.terminal.is_running())

    def _run_state_changed(self, running: bool) -> None:
        self.stop_action.setEnabled(running)
        self._update_run_target()
