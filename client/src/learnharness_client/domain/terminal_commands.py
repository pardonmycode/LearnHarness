"""The few commands children can type. Nothing here reaches a system shell."""

from __future__ import annotations

import os
import shlex
from dataclasses import dataclass
from pathlib import Path

from ..texts import T
from .path_guard import PathNotAllowed
from .project import Project
from .run_target import RunTarget, find_python


@dataclass(frozen=True, slots=True)
class CommandResult:
    output: str = ""
    target: RunTarget | None = None
    clear: bool = False


class CommandShell:
    """Keeps the current folder and turns a typed line into a result."""

    def __init__(self, project: Project) -> None:
        self.project = project
        self.cwd = project.root

    def prompt(self) -> str:
        relative = self.cwd.relative_to(self.project.root).as_posix()
        folder = (
            self.project.root.name if relative == "." else f"{self.project.root.name}/{relative}"
        )
        return f"{folder} $ "

    def welcome(self) -> str:
        example = "godot" if self.project.language == "gdscript" else "python main.py"
        return T.TERMINAL_WELCOME.format(example=example)

    def execute(self, line: str, godot: str = "") -> CommandResult:
        try:
            # A Windows habit like "python game\main.py" should simply work.
            words = shlex.split(line.replace("\\", "/"))
        except ValueError:
            return CommandResult(T.TERMINAL_BAD_QUOTES)
        if not words:
            return CommandResult()
        command, arguments = words[0], words[1:]
        name = command.casefold()
        if name in ("python", "python3", "py"):
            return self._python(arguments)
        if name == "godot":
            return self._godot(godot)
        if name in ("ls", "dir"):
            return CommandResult(self._list())
        if name == "cd":
            return self._change_folder(arguments)
        if name == "pwd":
            return CommandResult(self.prompt().removesuffix(" $ "))
        if name in ("clear", "cls"):
            return CommandResult(clear=True)
        if name in ("help", "hilfe"):
            return CommandResult(T.TERMINAL_HELP)
        return CommandResult(T.TERMINAL_UNKNOWN.format(command=command))

    def _python(self, arguments: list[str]) -> CommandResult:
        if self.project.language != "python":
            return CommandResult(T.TERMINAL_PYTHON_IN_GODOT)
        if not arguments:
            return CommandResult(T.TERMINAL_PYTHON_NEEDS_FILE)
        file = arguments[0]
        if file.startswith("-"):
            return CommandResult(T.TERMINAL_NO_OPTIONS.format(option=file))
        path = Path(os.path.normpath(self.cwd / file))
        if not path.exists():
            with_suffix = path.with_name(path.name + ".py")
            if with_suffix.is_file():
                suggestion = f"{file}.py"
                return CommandResult(
                    T.TERMINAL_DID_YOU_MEAN.format(file=file, suggestion=suggestion)
                )
            return CommandResult(T.TERMINAL_FILE_MISSING.format(file=file))
        try:
            script = self.project.guard.ensure_allowed(path)
        except PathNotAllowed as exc:
            return CommandResult(str(exc))
        python = find_python()
        if python is None:
            return CommandResult(T.TERMINAL_NO_PYTHON)
        program, prefix = python
        # -u: prompts from input() and prints appear immediately.
        run_arguments = (*prefix, "-u", str(script), *arguments[1:])
        target = RunTarget(program, run_arguments, self.cwd, self.project.root, True)
        return CommandResult(target=target)

    def _godot(self, godot: str) -> CommandResult:
        if self.project.language != "gdscript":
            return CommandResult(T.TERMINAL_GODOT_IN_PYTHON)
        if not godot:
            return CommandResult(T.GODOT_NOT_SET)
        root = self.project.root
        return CommandResult(target=RunTarget(godot, ("--path", str(root)), root, root, False))

    def _list(self) -> str:
        guard = self.project.guard
        folders, files = [], []
        for child in sorted(self.cwd.iterdir(), key=lambda item: item.name.casefold()):
            if child.is_symlink():
                continue
            if child.is_dir():
                if not guard.skips_folder(child):
                    folders.append(f"{child.name}/")
            elif child.suffix.casefold() in guard.allowed_suffixes:
                files.append(child.name)
        return "\n".join(folders + files) or T.TERMINAL_EMPTY_FOLDER

    def _change_folder(self, arguments: list[str]) -> CommandResult:
        if not arguments:
            self.cwd = self.project.root
            return CommandResult()
        try:
            self.cwd = self.project.guard.ensure_folder(self.cwd / arguments[0])
        except PathNotAllowed as exc:
            return CommandResult(str(exc))
        return CommandResult()
