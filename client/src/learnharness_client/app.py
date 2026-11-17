"""Application startup, logging, and last-resort recovery."""

from __future__ import annotations

import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

from learnharness_client.config import AppSettings, app_data_dir
from learnharness_client.domain.project import GodotProject
from learnharness_client.net.fake_tutor_client import FakeTutorClient
from learnharness_client.net.http_tutor_client import HttpTutorClient
from learnharness_client.ui.dialogs.login_dialog import LoginDialog
from learnharness_client.ui.main_window import MainWindow
from learnharness_client.ui.theme import apply_theme

LOG = logging.getLogger(__name__)


def configure_logging() -> Path:
    log_dir = app_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "learnharness.log"
    handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    return log_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LearnHarness Godot learning client")
    parser.add_argument("--project", type=Path, help="Godot project to open")
    parser.add_argument("--server", help="Learning server base URL")
    parser.add_argument(
        "--fake-server",
        action="store_true",
        help="Use the built-in pedagogical fake server",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    QCoreApplication.setOrganizationName("LearnHarness")
    QCoreApplication.setApplicationName("LearnHarnessClient")
    app = QApplication(sys.argv[:1])
    settings = AppSettings()
    apply_theme(app, settings.font_size, settings.theme)
    configure_logging()

    login = LoginDialog(settings)
    if login.exec() != QDialog.DialogCode.Accepted or login.selected_profile is None:
        return 0
    student_profile = login.selected_profile

    server_url = args.server or settings.server_url
    use_fake = args.fake_server or (args.server is None and settings.use_fake_server)
    tutor_client = FakeTutorClient() if use_fake else HttpTutorClient(server_url)
    window = MainWindow(
        settings,
        tutor_client,
        student_profile,
        server_url=server_url,
    )

    previous_hook = sys.excepthook

    def exception_hook(exc_type, exc_value, traceback) -> None:
        LOG.critical(
            "Unhandled exception: %s", exc_type.__name__, exc_info=(exc_type, exc_value, traceback)
        )
        try:
            window.editor_tabs.write_recovery_drafts()
            QMessageBox.critical(
                window,
                "Etwas ist schiefgegangen",
                "Dein ungespeicherter Text wurde als Entwurf gesichert. "
                "Bitte starte LearnHarness neu.",
            )
        finally:
            previous_hook(exc_type, exc_value, traceback)

    sys.excepthook = exception_hook
    if args.project:
        try:
            window.open_project(GodotProject.open(args.project))
        except (OSError, ValueError) as exc:
            QMessageBox.warning(window, "Projekt nicht geöffnet", str(exc))
    else:
        # Children should land directly in their game; the last project opens automatically.
        for recent in settings.recent_projects:
            try:
                window.open_project(GodotProject.open(recent))
                break
            except (OSError, ValueError):
                continue
    window.show()
    return app.exec()
