"""Application startup, logging, and last-resort recovery."""

from __future__ import annotations

import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PyQt6.QtCore import QCoreApplication, QTimer
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

from learnharness_client.admin_sync import AdminSync, SyncResult
from learnharness_client.config import AppSettings, app_data_dir
from learnharness_client.domain.project import GodotProject
from learnharness_client.godot.project_list import known_godot_projects
from learnharness_client.net.fake_tutor_client import FakeTutorClient
from learnharness_client.net.http_tutor_client import HttpTutorClient
from learnharness_client.ui.dialogs.first_start_dialog import FirstStartDialog
from learnharness_client.ui.dialogs.login_dialog import LoginDialog
from learnharness_client.ui.main_window import MainWindow
from learnharness_client.ui.project_picker import choose_project
from learnharness_client.ui.theme import apply_theme

from .texts import T

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


def _offer_known_projects(window: MainWindow, known: list[Path]) -> None:
    project = choose_project(window, recent=window.settings.recent_projects, known=known)
    if project is not None:
        window.open_project(project)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    QCoreApplication.setOrganizationName("LearnHarness")
    QCoreApplication.setApplicationName("LearnHarnessClient")
    app = QApplication(sys.argv[:1])
    settings = AppSettings()
    apply_theme(app, settings.font_size, settings.theme)
    configure_logging()

    if not settings.first_start_done and not (args.server or args.fake_server):
        FirstStartDialog(settings).exec()

    # Central administration (optional): take over profiles and levels before the login.
    admin_sync = AdminSync.from_settings(settings)
    sync_result = admin_sync.sync_at_start() if admin_sync else SyncResult.DISABLED

    login = LoginDialog(settings)
    if login.exec() != QDialog.DialogCode.Accepted or login.selected_profile is None:
        return 0
    student_profile = login.selected_profile
    if admin_sync is not None:
        admin_sync.register(student_profile)  # harmless if the server already knows it

    server_url = args.server or settings.server_url
    use_fake = args.fake_server or (args.server is None and settings.use_fake_server)
    tutor_client = FakeTutorClient() if use_fake else HttpTutorClient(server_url)
    window = MainWindow(
        settings,
        tutor_client,
        student_profile,
        server_url=server_url,
        admin_sync=admin_sync,
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
                T.CRASH_TITLE,
                T.CRASH,
            )
        finally:
            previous_hook(exc_type, exc_value, traceback)

    sys.excepthook = exception_hook
    if args.project:
        try:
            window.open_project(GodotProject.open(args.project))
        except (OSError, ValueError) as exc:
            QMessageBox.warning(window, T.PROJECT_NOT_OPENED, str(exc))
    else:
        # Children should land directly in their game; the last project opens automatically.
        for recent in settings.recent_projects:
            try:
                window.open_project(GodotProject.open(recent))
                break
            except (OSError, ValueError):
                continue
    window.show()
    if sync_result in (SyncResult.OFFLINE, SyncResult.UNAUTHORIZED):
        window.statusBar().showMessage(T.ADMIN_START_OFFLINE, 15_000)
    if window.project is None:
        known = known_godot_projects()
        if known:
            # First start: suggest the projects Godot already knows instead of a folder dialog.
            QTimer.singleShot(0, lambda: _offer_known_projects(window, known))
    QTimer.singleShot(300, window.show_tutorial_once)
    return app.exec()
