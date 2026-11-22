"""What the terminal needs from the main window."""

from __future__ import annotations

from learnharness_client.godot.paths import find_godot_on_path


class RunActions:
    """Connects the terminal with the open files and the Godot setting."""

    def _save_open_files(self) -> bool:
        """Scripts import each other, so every open file must be on disk as shown."""
        for editor, document in list(self.editor_tabs.documents.items()):
            if document.dirty and not self.editor_tabs.save_editor(editor):
                return False
        return True

    def _godot_program(self) -> str:
        return self.settings.godot_path or find_godot_on_path()
