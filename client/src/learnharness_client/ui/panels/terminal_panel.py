"""Small terminal that runs the project and shows its output. It is not a free shell."""

from __future__ import annotations

import codecs
import re

from PyQt6.QtCore import QProcess, QProcessEnvironment, QTimer, pyqtSignal
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from learnharness_client.domain.run_target import RunTarget

from ...texts import T
from ..theme import monospace_font

MAX_LINES = 2000
MAX_CHARACTERS = 200_000
MAX_PENDING = 32_000  # an endless print loop must not freeze the window
FLUSH_MS = 40
_ANSI_CODE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


class TerminalPanel(QWidget):
    run_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    running_changed = pyqtSignal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._pending = ""
        self._dropped = False
        self._stopped = False
        self._failed_to_start = False
        self._can_start = False
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
        self.start_button = QPushButton(T.TERMINAL_START_EMPTY)
        self.start_button.setProperty("primary", "true")
        self.start_button.clicked.connect(self.run_requested)
        self.stop_button = QPushButton(T.TERMINAL_STOP)
        self.stop_button.clicked.connect(self.stop_requested)
        clear_button = QPushButton(T.TERMINAL_CLEAR)
        self.output = QPlainTextEdit()
        self.output.setObjectName("codeView")
        self.output.setReadOnly(True)
        self.output.setFont(monospace_font(12))
        self.output.setMaximumBlockCount(MAX_LINES)
        self.output.setAccessibleName(T.TERMINAL_OUTPUT_A11Y)
        self.output.setPlaceholderText(T.TERMINAL_IDLE)
        clear_button.clicked.connect(self.output.clear)
        self.input = QLineEdit()
        self.input.setFont(monospace_font(12))
        self.input.setPlaceholderText(T.TERMINAL_INPUT_PLACEHOLDER)
        self.input.setAccessibleName(T.TERMINAL_INPUT_A11Y)
        self.input.returnPressed.connect(self._send_input)

        header = QHBoxLayout()
        header.addWidget(heading)
        header.addStretch(1)
        header.addWidget(clear_button)
        header.addWidget(self.stop_button)
        header.addWidget(self.start_button)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(6)
        layout.addLayout(header)
        layout.addWidget(self.output, 1)
        layout.addWidget(self.input)
        self.setMinimumHeight(150)
        self._sync_controls()

    def is_running(self) -> bool:
        return self.process.state() != QProcess.ProcessState.NotRunning

    def set_start_label(self, text: str, *, enabled: bool) -> None:
        self.start_button.setText(text)
        self._can_start = enabled
        self._sync_controls()

    def start(self, target: RunTarget) -> None:
        if self.is_running():
            return
        self.output.clear()
        self._pending = ""
        self._dropped = False
        self._stopped = False
        self._failed_to_start = False
        self._decoder.reset()
        self.show_message(T.TERMINAL_STARTED.format(file=target.label))
        environment = QProcessEnvironment.systemEnvironment()
        if target.is_python:
            environment.remove("PYTHONHOME")
            # Imports like "from game.player import Player" work from every script.
            environment.insert("PYTHONPATH", str(target.working_dir))
            environment.insert("PYTHONUTF8", "1")
            environment.insert("PYTHONIOENCODING", "utf-8")
            environment.insert("PYTHONDONTWRITEBYTECODE", "1")
        self.process.setProcessEnvironment(environment)
        self.process.setWorkingDirectory(str(target.working_dir))
        self.process.setProgram(target.program)
        self.process.setArguments(list(target.arguments))
        self._flush_timer.start()
        self.process.start()
        self._sync_controls()
        self.running_changed.emit(True)
        self.input.setFocus()

    def stop(self) -> None:
        if self.is_running():
            self._stopped = True
            self.process.kill()

    def shutdown(self) -> None:
        """Ends a running program before the project or the app closes."""
        if self.is_running():
            self.stop()
            self.process.waitForFinished(1500)

    def show_message(self, text: str) -> None:
        self._flush()
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        needs_break = bool(self.output.toPlainText()) and not self.output.toPlainText().endswith(
            "\n"
        )
        cursor.insertText(("\n" if needs_break else "") + text + "\n")
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def _send_input(self) -> None:
        if not self.is_running():
            return
        text = self.input.text()
        self.input.clear()
        self._append(text + "\n")
        self.process.write((text + "\n").encode("utf-8"))

    def _read_output(self) -> None:
        data = bytes(self.process.readAllStandardOutput())
        self._append(self._decoder.decode(data))

    def _append(self, text: str) -> None:
        self._pending += text
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
        bar = self.output.verticalScrollBar()
        follow = bar is None or bar.value() >= bar.maximum() - 2
        cursor = QTextCursor(self.output.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        if self.output.document().characterCount() > MAX_CHARACTERS:
            # One endless line never reaches the line limit.
            self.output.setPlainText(self.output.toPlainText()[-MAX_CHARACTERS // 2 :])
        if follow and bar is not None:
            bar.setValue(bar.maximum())

    def _process_error(self, error: QProcess.ProcessError) -> None:
        if error == QProcess.ProcessError.FailedToStart:
            self._failed_to_start = True
            self._flush_timer.stop()
            self.show_message(T.TERMINAL_NOT_STARTED)
            self._sync_controls()
            self.running_changed.emit(False)

    def _finished(self, code: int, status: QProcess.ExitStatus) -> None:
        self._read_output()
        self._append(self._decoder.decode(b"", final=True))
        self._flush_timer.stop()
        if self._stopped:
            self.show_message(T.TERMINAL_STOPPED)
        elif status == QProcess.ExitStatus.NormalExit and code == 0:
            self.show_message(T.TERMINAL_FINISHED)
        else:
            self.show_message(T.TERMINAL_FAILED.format(code=code))
        self._sync_controls()
        self.running_changed.emit(False)

    def _sync_controls(self) -> None:
        running = self.is_running()
        self.start_button.setEnabled(self._can_start and not running)
        self.stop_button.setEnabled(running)
        self.input.setEnabled(running)
