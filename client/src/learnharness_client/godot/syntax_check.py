"""Optional syntax check via ``godot --headless --check-only`` without blocking the UI."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QProcess, QTimer, pyqtSignal

from .output_parser import GodotMessage, parse_godot_output

TIMEOUT_MS = 10_000
MAX_OUTPUT_BYTES = 256 * 1024


class SyntaxChecker(QObject):
    """Runs one check at a time; ``finished`` carries the parsed messages."""

    finished = pyqtSignal(object)  # list[GodotMessage]
    failed = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.process: QProcess | None = None
        self._output = bytearray()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._timed_out)

    @staticmethod
    def arguments(project_root: Path, script: Path) -> list[str]:
        resource = "res://" + script.relative_to(project_root).as_posix()
        return [
            "--headless",
            "--path",
            str(project_root),
            "--check-only",
            "--script",
            resource,
        ]

    def is_running(self) -> bool:
        return self.process is not None

    def start(self, godot_executable: str, project_root: Path, script: Path) -> bool:
        if self.process is not None:
            return False
        if not godot_executable or not Path(godot_executable).is_file():
            self.failed.emit("Das Godot-Programm wurde nicht gefunden.")
            return False
        process = QProcess(self)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.setWorkingDirectory(str(project_root))
        process.readyReadStandardOutput.connect(self._read_output)
        process.finished.connect(self._process_finished)
        process.errorOccurred.connect(self._process_error)
        self.process = process
        self._output.clear()
        process.start(godot_executable, self.arguments(project_root, script))
        self._timer.start(TIMEOUT_MS)
        return True

    def _read_output(self) -> None:
        if self.process is None:
            return
        chunk = bytes(self.process.readAllStandardOutput())
        room = MAX_OUTPUT_BYTES - len(self._output)
        if room > 0:
            self._output.extend(chunk[:room])

    def _process_finished(self, *_args) -> None:
        if self.process is None:
            return
        self._read_output()
        text = self._output.decode("utf-8", errors="replace")
        self._cleanup()
        messages: list[GodotMessage] = parse_godot_output(text)
        self.finished.emit(messages)

    def _process_error(self, error: QProcess.ProcessError) -> None:
        if error == QProcess.ProcessError.FailedToStart:
            self._cleanup()
            self.failed.emit("Godot ließ sich nicht starten.")

    def _timed_out(self) -> None:
        if self.process is None:
            return
        process = self.process
        self._cleanup()
        process.kill()
        self.failed.emit("Godot hat nicht innerhalb von 10 Sekunden geantwortet.")

    def _cleanup(self) -> None:
        self._timer.stop()
        process = self.process
        self.process = None
        if process is not None:
            process.finished.disconnect(self._process_finished)
            process.deleteLater()
