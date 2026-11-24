"""Terminal without buttons: children type commands such as ``python main.py``."""

from __future__ import annotations

import codecs
import re
from collections.abc import Callable

from PyQt6.QtCore import QProcess, QProcessEnvironment, QTimer, pyqtSignal
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from learnharness_client import design
from learnharness_client.domain.project import Project
from learnharness_client.domain.run_error import find_run_error, hide_private_paths
from learnharness_client.domain.run_target import RunTarget
from learnharness_client.domain.terminal_commands import CommandShell

from ...texts import T
from .terminal_console import TerminalConsole

MAX_PENDING = 32_000  # an endless print loop must not freeze the window
FLUSH_MS = 40
MAX_ERROR_SCAN = 16_000  # the end of the output, where an error stands
_ANSI_CODE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


class TerminalPanel(QWidget):
    run_succeeded = pyqtSignal()

    def __init__(
        self,
        before_run: Callable[[], bool],
        godot_program: Callable[[], str],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._before_run = before_run
        self._godot_program = godot_program
        self.shell: CommandShell | None = None
        self._pending = ""
        self._dropped = False
        self._stopped = False
        self._target: RunTarget | None = None
        self._run_output = ""
        self.last_error: str | None = None
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._process_error)
        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(FLUSH_MS)
        self._flush_timer.timeout.connect(self._flush)

        heading = QLabel(T.TERMINAL_HEADING)
        heading.setProperty("role", "section")
        self.console = TerminalConsole()
        self.console.line_entered.connect(self._line_entered)
        self.console.interrupt_requested.connect(self._interrupt)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*design.TERMINAL_MARGINS)
        layout.setSpacing(design.TERMINAL_SPACING)
        layout.addWidget(heading)
        layout.addWidget(self.console, 1)
        self.setMinimumHeight(design.TERMINAL_MIN_HEIGHT)
        self.setFocusProxy(self.console)
        self.console.write(T.TERMINAL_NO_PROJECT + "\n")

    def set_project(self, project: Project) -> None:
        self.shutdown()
        self.last_error = None
        self.shell = CommandShell(project)
        self.console.reset()
        self.console.write(self.shell.welcome() + "\n")
        self._write_prompt()

    def is_running(self) -> bool:
        return self.process.state() != QProcess.ProcessState.NotRunning

    def shutdown(self) -> None:
        """Ends a running program before the project or the app closes."""
        if self.is_running():
            self._stopped = True
            self.process.kill()
            self.process.waitForFinished(1500)

    # Commands -------------------------------------------------------------------------

    def _line_entered(self, text: str) -> None:
        if self.is_running():
            self.process.write((text + "\n").encode("utf-8"))
            return
        if self.shell is None:
            self.console.write(T.TERMINAL_NO_PROJECT + "\n")
            return
        result = self.shell.execute(text, self._godot_program())
        if result.clear:
            self.console.reset()
        if result.output:
            self.console.write(result.output + "\n")
        if result.target is None:
            self._write_prompt()
        elif self._before_run():
            self._start(result.target)
        else:
            self._write_prompt()

    def _interrupt(self) -> None:
        if self.is_running():
            self._stopped = True
            self.process.kill()
        elif self.shell is not None:
            self.console.write("^C\n")
            self.console.focus_input()
            self._write_prompt()

    def _write_prompt(self) -> None:
        if self.shell is None:
            return
        if not self.console.at_line_start():
            self.console.write("\n")
        self.console.write(self.shell.prompt())
        self.console.focus_input()

    # The running program --------------------------------------------------------------

    def _start(self, target: RunTarget) -> None:
        self._target = target
        self._run_output = ""
        self._pending = ""
        self._dropped = False
        self._stopped = False
        self._decoder.reset()
        environment = QProcessEnvironment.systemEnvironment()
        if target.is_python:
            environment.remove("PYTHONHOME")
            # Imports like "from game.player import Player" work from every script.
            environment.insert("PYTHONPATH", str(target.project_root))
            environment.insert("PYTHONUTF8", "1")
            environment.insert("PYTHONIOENCODING", "utf-8")
            environment.insert("PYTHONDONTWRITEBYTECODE", "1")
        self.process.setProcessEnvironment(environment)
        self.process.setWorkingDirectory(str(target.working_dir))
        self.process.setProgram(target.program)
        self.process.setArguments(list(target.arguments))
        self._flush_timer.start()
        self.process.start()

    def _read_output(self) -> None:
        self._append(self._decoder.decode(bytes(self.process.readAllStandardOutput())))

    def _append(self, text: str) -> None:
        self._pending += text
        self._run_output = (self._run_output + text)[-MAX_ERROR_SCAN:]
        if len(self._pending) > MAX_PENDING:
            self._pending = self._pending[-MAX_PENDING:]
            self._dropped = True

    def _flush(self) -> None:
        if not self._pending and not self._dropped:
            return
        text = _ANSI_CODE.sub("", self._pending).replace("\r\n", "\n").replace("\r", "\n")
        if self._dropped:
            text = f"\n{T.TERMINAL_TOO_MUCH}\n{text}"
        self._pending = ""
        self._dropped = False
        self.console.write(text)

    def _process_error(self, error: QProcess.ProcessError) -> None:
        if error == QProcess.ProcessError.FailedToStart:
            self._flush_timer.stop()
            self.console.write(T.TERMINAL_NOT_STARTED + "\n")
            self._write_prompt()

    def _remember_result(self, code: int) -> None:
        """The latest error for the tutor; a run without one makes older errors obsolete."""
        target = self._target
        if target is None:
            return
        output = _ANSI_CODE.sub("", self._run_output).replace("\r\n", "\n").replace("\r", "\n")
        found = find_run_error(output, is_python=target.is_python, exit_code=code)
        self.last_error = hide_private_paths(found, target.project_root) if found else None
        if found is None and code == 0 and not self._stopped:
            self.run_succeeded.emit()

    def _finished(self, code: int, _status: QProcess.ExitStatus) -> None:
        self._read_output()
        self._append(self._decoder.decode(b"", final=True))
        self._flush_timer.stop()
        self._flush()
        self._remember_result(code)
        if self._stopped:
            if not self.console.at_line_start():
                self.console.write("\n")
            self.console.write(T.TERMINAL_STOPPED + "\n")
        self._write_prompt()
