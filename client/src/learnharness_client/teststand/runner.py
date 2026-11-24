"""Starts the local learning server and the app for the test stand, step by step."""

from __future__ import annotations

import socket
import sys
from collections.abc import Callable
from importlib.util import find_spec
from pathlib import Path

from PyQt6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, pyqtSignal

from .config import DATA_DIR, TeststandConfig, prepare_arguments, server_environment

REQUIRED_PACKAGES = (
    "django",
    "daphne",
    "channels",
    "whitenoise",
    "anthropic",
    "openai",
    "learnharness_protocol",
)
INSTALL_HINT = 'python -m pip install -e ./protocol -e ./client -e "./server[dev]"'
READY_TIMEOUT_MS = 40_000
POLL_MS = 300
TAIL_CHARS = 4000


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False


def setup_problem() -> str | None:
    if not (repository_root() / "server" / "manage.py").is_file():
        return "Der Teststand läuft nur aus dem LearnHarness-Repository (server/ fehlt)."
    missing = [name for name in REQUIRED_PACKAGES if find_spec(name) is None]
    if missing:
        return f"Es fehlen Pakete ({', '.join(missing)}). Installiere sie mit:\n{INSTALL_HINT}"
    return None


def _environment(extra: dict[str, str]) -> QProcessEnvironment:
    environment = QProcessEnvironment.systemEnvironment()
    for name, value in extra.items():
        environment.insert(name, value)
    return environment


class StandRunner(QObject):
    status = pyqtSignal(str)
    failed = pyqtSignal(str)
    ready = pyqtSignal(str)  # address of the local learning server
    check_done = pyqtSignal(bool, str)

    def __init__(self, data_dir: Path = DATA_DIR, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.data_dir = data_dir
        self.server: QProcess | None = None
        self.client: QProcess | None = None
        self.url = ""
        self._step: QProcess | None = None
        self._tail = ""
        self._port = 0
        self._waited = 0
        self._poll = QTimer(self)
        self._poll.setInterval(POLL_MS)
        self._poll.timeout.connect(self._wait_for_server)

    @property
    def log_file(self) -> Path:
        return self.data_dir / "server.log"

    @property
    def database(self) -> Path:
        return self.data_dir / "server.sqlite3"

    # Steps -----------------------------------------------------------------------------

    def _process(self, env: dict[str, str]) -> QProcess:
        process = QProcess(self)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.setWorkingDirectory(str(repository_root() / "server"))
        process.setProcessEnvironment(_environment(env))
        process.readyReadStandardOutput.connect(lambda: self._collect(process))
        return process

    def _collect(self, process: QProcess) -> None:
        text = bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
        self._tail = (self._tail + text)[-TAIL_CHARS:]
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with self.log_file.open("a", encoding="utf-8") as log:
            log.write(text)

    def _run_steps(
        self, config: TeststandConfig, steps: list[list[str]], then: Callable[[], None]
    ) -> None:
        if not steps:
            then()
            return
        self._tail = ""
        step = self._process(server_environment(config, self.data_dir))
        self._step = step

        def finished(code: int, _status: QProcess.ExitStatus) -> None:
            self._step = None
            if code != 0:
                self.failed.emit(self._tail.strip() or f"{steps[0][0]} ist fehlgeschlagen.")
                return
            self._run_steps(config, steps[1:], then)

        step.finished.connect(finished)
        step.start(sys.executable, ["manage.py", *steps[0]])

    def _setup_steps(self, config: TeststandConfig) -> list[list[str]]:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return [["migrate", "--noinput"], ["teststand_prepare", *prepare_arguments(config)]]

    # Public ----------------------------------------------------------------------------

    def check(self, config: TeststandConfig) -> None:
        def run_check() -> None:
            self._tail = ""
            step = self._process(server_environment(config, self.data_dir))
            self._step = step
            step.finished.connect(
                lambda code, _status: self.check_done.emit(code == 0, self._tail.strip())
            )
            step.start(sys.executable, ["manage.py", "teststand_check"])

        self.status.emit("Prüfe die Verbindung zur KI …")
        self._run_steps(config, self._setup_steps(config), run_check)

    def start(self, config: TeststandConfig) -> None:
        self.stop()
        self.status.emit("Richte den lokalen Lernserver ein …")
        self._run_steps(config, self._setup_steps(config), lambda: self._start_server(config))

    def _start_server(self, config: TeststandConfig) -> None:
        self._port = free_port()
        self.url = f"http://127.0.0.1:{self._port}"
        self._tail = ""
        self.server = self._process(server_environment(config, self.data_dir))
        self.server.finished.connect(self._server_finished)
        self.server.start(
            sys.executable, ["manage.py", "runserver", f"127.0.0.1:{self._port}", "--noreload"]
        )
        self.status.emit("Starte den lokalen Lernserver …")
        self._waited = 0
        self._poll.start()

    def _wait_for_server(self) -> None:
        self._waited += POLL_MS
        if port_open(self._port):
            self._poll.stop()
            self.ready.emit(self.url)
            self._start_client()
        elif self._waited >= READY_TIMEOUT_MS:
            self._poll.stop()
            self.failed.emit("Der lokale Lernserver startet nicht.\n" + self._tail.strip())
            self.stop()

    def _server_finished(self, _code: int, _status: QProcess.ExitStatus) -> None:
        if self.server is not None:  # not stopped on purpose
            self._poll.stop()
            self.server = None
            self.failed.emit("Der lokale Lernserver wurde beendet.\n" + self._tail.strip())

    def _start_client(self) -> None:
        # The app keeps profiles and settings in the test stand folder; it never sees the keys.
        client = QProcess(self)
        client.setProcessEnvironment(
            _environment({"LEARNHARNESS_DATA_DIR": str(self.data_dir / "client")})
        )
        client.setProcessChannelMode(QProcess.ProcessChannelMode.ForwardedChannels)
        client.start(sys.executable, ["-m", "learnharness_client", "--server", self.url])
        self.client = client
        self.status.emit(f"Läuft: Die App ist mit {self.url} verbunden.")

    def stop(self) -> None:
        self._poll.stop()
        for name in ("client", "server", "_step"):
            process = getattr(self, name)
            setattr(self, name, None)
            if process is not None and process.state() != QProcess.ProcessState.NotRunning:
                process.kill()
                process.waitForFinished(3000)
