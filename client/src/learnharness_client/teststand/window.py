"""The test stand window: choose the AI, start server and app, read every prompt."""

from __future__ import annotations

import shutil
from pathlib import Path

from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtGui import QCloseEvent, QDesktopServices
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from . import config as stand_config
from .config import DATA_DIR, TeststandConfig
from .log_view import LogView
from .runner import StandRunner, setup_problem

PROVIDERS = (("anthropic", "Claude (Anthropic)"), ("vllm", "Lokales Modell (vLLM)"))
EFFORTS = (("low", "niedrig"), ("medium", "mittel"), ("high", "hoch"), ("", "Standard"))
LINKS = (
    ("KI-Protokoll im Admin", "/admin/tutor/aicall/"),
    ("Prompt-Übersicht", "/ki/prompts/"),
    ("Kinder und Stufen", "/admin/children/child/"),
)
CHECK_OK = "Verbindung klappt: "  # first words of teststand_check on success


class TeststandWindow(QMainWindow):
    __test__ = False  # not a pytest class despite the name

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        super().__init__()
        self.setWindowTitle("LearnHarness-Teststand")
        self.resize(1300, 820)
        self.data_dir = data_dir
        self.config = stand_config.load(data_dir)
        self.runner = StandRunner(data_dir, self)
        self.runner.status.connect(self._set_status)
        self.runner.failed.connect(self._failed)
        self.runner.ready.connect(self._ready)
        self.runner.check_done.connect(self._checked)

        self.provider = QComboBox()
        for key, label in PROVIDERS:
            self.provider.addItem(label, key)
        self.pages = QStackedWidget()
        self.anthropic_key = self._secret("sk-ant-…")
        self.anthropic_model = QLineEdit()
        self.anthropic_effort = QComboBox()
        for key, label in EFFORTS:
            self.anthropic_effort.addItem(label, key)
        self.vllm_url = QLineEdit()
        self.vllm_model = QLineEdit()
        self.vllm_model.setPlaceholderText("leer lassen: das erste Modell des Servers")
        self.vllm_key = self._secret("nur falls dein vLLM einen Schlüssel verlangt")
        self.pages.addWidget(
            self._page(
                ("API-Schlüssel", self.anthropic_key),
                ("Modell", self.anthropic_model),
                ("Denkaufwand", self.anthropic_effort),
            )
        )
        self.pages.addWidget(
            self._page(
                ("Adresse", self.vllm_url),
                ("Modell", self.vllm_model),
                ("Schlüssel", self.vllm_key),
            )
        )
        self.provider.currentIndexChanged.connect(self.pages.setCurrentIndex)
        self.remember = QCheckBox("Schlüssel auf diesem Rechner merken (nur für dich lesbar)")
        self.check_button = QPushButton("Verbindung testen")
        self.start_button = QPushButton("Starten")
        self.start_button.setProperty("primary", "true")
        self.stop_button = QPushButton("Stoppen")
        self.reset_button = QPushButton("Testdaten löschen")
        self.check_button.clicked.connect(lambda: self._run(self.runner.check))
        self.start_button.clicked.connect(lambda: self._run(self.runner.start))
        self.stop_button.clicked.connect(self._stop)
        self.reset_button.clicked.connect(self._reset)
        self.status = QLabel("Trage einen Anbieter ein und klicke auf Starten.")
        self.status.setWordWrap(True)
        self.admin = QLabel()
        self.admin.setWordWrap(True)
        self.links = [QPushButton(label) for label, _path in LINKS]
        for button, (_label, path) in zip(self.links, LINKS, strict=True):
            button.clicked.connect(lambda _=False, p=path: self._open(p))
            button.setEnabled(False)

        form = QFormLayout()
        form.addRow("Anbieter", self.provider)
        buttons = QHBoxLayout()
        for button in (self.check_button, self.start_button, self.stop_button):
            buttons.addWidget(button)
        side = QWidget()
        side_layout = QVBoxLayout(side)
        side_layout.addLayout(form)
        side_layout.addWidget(self.pages)
        side_layout.addWidget(self.remember)
        side_layout.addLayout(buttons)
        side_layout.addWidget(self.status)
        side_layout.addWidget(self.admin)
        for button in self.links:
            side_layout.addWidget(button)
        side_layout.addStretch(1)
        side_layout.addWidget(self.reset_button)
        self.log = LogView()
        splitter = QSplitter()
        splitter.addWidget(side)
        splitter.addWidget(self.log)
        splitter.setSizes([380, 920])
        self.setCentralWidget(splitter)
        self._fill_form()
        self._timer = QTimer(self)
        self._timer.setInterval(1500)
        self._timer.timeout.connect(lambda: self.log.poll(self.runner.database))
        self._timer.start()
        self.log.poll(self.runner.database)

    @staticmethod
    def _secret(placeholder: str) -> QLineEdit:
        field = QLineEdit()
        field.setEchoMode(QLineEdit.EchoMode.Password)
        field.setPlaceholderText(placeholder)
        return field

    @staticmethod
    def _page(*rows: tuple[str, QWidget]) -> QWidget:
        page = QWidget()
        layout = QFormLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        for label, widget in rows:
            layout.addRow(label, widget)
        return page

    def _fill_form(self) -> None:
        c = self.config
        self.provider.setCurrentIndex(max(0, self.provider.findData(c.provider)))
        self.pages.setCurrentIndex(self.provider.currentIndex())
        self.anthropic_key.setText(c.anthropic_key)
        self.anthropic_model.setText(c.anthropic_model)
        self.anthropic_effort.setCurrentIndex(
            max(0, self.anthropic_effort.findData(c.anthropic_effort))
        )
        self.vllm_url.setText(c.vllm_url)
        self.vllm_model.setText(c.vllm_model)
        self.vllm_key.setText(c.vllm_key)
        self.remember.setChecked(c.remember_keys)

    def read_form(self) -> TeststandConfig:
        c = self.config
        c.provider = str(self.provider.currentData())
        c.anthropic_key = self.anthropic_key.text().strip()
        c.anthropic_model = self.anthropic_model.text().strip()
        c.anthropic_effort = str(self.anthropic_effort.currentData())
        c.vllm_url = self.vllm_url.text().strip()
        c.vllm_model = self.vllm_model.text().strip()
        c.vllm_key = self.vllm_key.text().strip()
        c.remember_keys = self.remember.isChecked()
        return c

    def _run(self, action) -> None:  # type: ignore[no-untyped-def]
        config = self.read_form()
        problem = setup_problem() or config.problem()
        if problem:
            self._failed(problem)
            return
        stand_config.save(config, self.data_dir)
        action(config)

    def _set_status(self, text: str) -> None:
        self.status.setText(text)

    def _failed(self, text: str) -> None:
        self.status.setText("Fehler: " + text[-1500:])
        for button in self.links:
            button.setEnabled(False)

    def _ready(self, url: str) -> None:
        self.admin.setText(
            f"Lernserver: {url}\nAdmin-Anmeldung: teststand / {self.config.admin_password}"
        )
        self.admin.setTextInteractionFlags(self.admin.textInteractionFlags())
        for button in self.links:
            button.setEnabled(True)

    def _checked(self, ok: bool, text: str) -> None:
        last = text.strip().splitlines()[-1] if text.strip() else ""
        model = last.removeprefix(CHECK_OK) if ok and last.startswith(CHECK_OK) else ""
        if model and self.provider.currentData() == "vllm":
            # The server took the first model of vLLM; show it, so the form says what runs.
            self.vllm_model.setText(model)
            stand_config.save(self.read_form(), self.data_dir)
        self.status.setText(("✓ " if ok else "Fehler: ") + (last or "keine Antwort"))

    def _open(self, path: str) -> None:
        if self.runner.url:
            QDesktopServices.openUrl(QUrl(self.runner.url + path))

    def _stop(self) -> None:
        self.runner.stop()
        self.status.setText("Gestoppt.")
        for button in self.links:
            button.setEnabled(False)

    def _reset(self) -> None:
        answer = QMessageBox.question(
            self,
            "Testdaten löschen",
            "Lernserver-Daten und Profile des Teststands löschen? Deine Projekte bleiben.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._stop()
        self.runner.database.unlink(missing_ok=True)
        shutil.rmtree(self.data_dir / "client", ignore_errors=True)
        self.log.reset()
        self.status.setText("Testdaten gelöscht.")

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt API
        stand_config.save(self.read_form(), self.data_dir)
        self.runner.stop()
        event.accept()
