"""Main application window tying safe editing and tutoring together."""

from __future__ import annotations

import logging

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QDockWidget, QLabel, QMainWindow, QSplitter, QTabWidget

from learnharness_client.admin_sync import AdminSync
from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import StudentProfile
from learnharness_client.domain.project import Project
from learnharness_client.godot.syntax_check import SyntaxChecker
from learnharness_client.net.connection_monitor import ConnectionMonitor
from learnharness_client.net.tutor_client import TutorClient

from ...texts import T
from ..editor.editor_tabs import EditorTabs
from ..panels.diagnostics_panel import DiagnosticsPanel
from ..panels.explain_panel import ExplainPanel
from ..panels.learn_agent_panel import LearnAgentPanel
from ..panels.mission_panel import MissionPanel
from ..panels.problems_panel import ProblemsPanel
from ..panels.progress_panel import ProgressPanel
from ..panels.project_panel import ProjectPanel
from ..panels.tutor_panel import TutorPanel
from ..script_tree import ScriptTree
from ..theme import set_state
from .actions import WindowActions
from .checks import CheckActions
from .constants import GODOT_TASK_ID, MAX_FILE_CONTEXT, PYTHON_TASK_ID, is_target_file
from .explain_missions import ExplainMissionActions
from .learning import LearningActions
from .projects import ProjectActions
from .responses import ServerResponses
from .window_dialogs import WindowDialogs

__all__ = [
    "GODOT_TASK_ID",
    "LOG",
    "MAX_FILE_CONTEXT",
    "MainWindow",
    "PYTHON_TASK_ID",
    "is_target_file",
]


LOG = logging.getLogger(__name__)


class MainWindow(
    WindowActions,
    ProjectActions,
    ExplainMissionActions,
    LearningActions,
    ServerResponses,
    WindowDialogs,
    CheckActions,
    QMainWindow,
):
    def __init__(
        self,
        settings: AppSettings,
        tutor_client: TutorClient,
        student_profile: StudentProfile,
        *,
        server_url: str,
        admin_sync: AdminSync | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.settings = settings
        self.tutor_client = tutor_client
        self.student_profile = student_profile
        self.server_url = server_url
        self.project: Project | None = None
        self.session_id: str | None = None
        self.current_task_id = GODOT_TASK_ID
        self.learn_round_active = False
        self._awaiting_learn_response = False
        self._learn_target_file: str | None = None
        self.active_learning_level = 1
        self.admin_sync = admin_sync
        # Which panel waits for the next tutor answer / owns the exercise on screen.
        # None means the tutor chat.
        self._response_owner: str | None = None
        self._exercise_owner = "agent"
        self._mission_target_file: str | None = None
        self.setWindowTitle(T.APP_TITLE)
        self.resize(1380, 840)

        self.script_tree = ScriptTree()
        self.editor_tabs = EditorTabs(settings)
        self.learn_agent_panel = LearnAgentPanel(
            settings.max_unlocked_learning_level(student_profile.profile_id),
            show_changes=settings.show_agent_changes,
        )
        self.tutor_panel = TutorPanel()
        self.progress_panel = ProgressPanel()
        self.explain_panel = ExplainPanel()
        self.project_panel = ProjectPanel()
        self._plan_project_id: str | None = None
        self.mission_panel = MissionPanel()
        self.mission_panel.restore(settings.mission_progress(student_profile.profile_id))

        learning_tabs = QTabWidget()
        learning_tabs.addTab(self.learn_agent_panel, T.TAB_AGENT)
        learning_tabs.addTab(self.project_panel, T.TAB_PROJECT)
        learning_tabs.addTab(self.mission_panel, T.TAB_MISSIONS)
        learning_tabs.addTab(self.explain_panel, T.TAB_EXPLAIN)
        learning_tabs.addTab(self.tutor_panel, T.TAB_TUTOR)
        learning_tabs.addTab(self.progress_panel, T.TAB_PROGRESS)
        self.learning_tabs = learning_tabs

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.script_tree)
        splitter.addWidget(self.editor_tabs)
        splitter.addWidget(learning_tabs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        splitter.setStretchFactor(2, 2)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([220, 700, 460])
        self.splitter = splitter
        self.setCentralWidget(splitter)

        self.problems_panel = ProblemsPanel()
        problems_dock = QDockWidget(T.PROBLEMS_DOCK, self)
        problems_dock.setObjectName("problemsDock")
        problems_dock.setWidget(self.problems_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, problems_dock)
        problems_dock.setVisible(False)
        self.problems_dock = problems_dock

        self.project_status = QLabel(T.NO_PROJECT)
        self.file_status = QLabel(T.NO_FILE)
        self.profile_status = QLabel(
            T.PROFILE.format(
                pseudonym=student_profile.pseudonym,
                experience=student_profile.experience_label,
            )
        )
        self.cursor_status = QLabel(T.CURSOR_EMPTY)
        self.connection_status = QLabel(T.CONNECTION_CHECKING)
        self.connection_status.setObjectName("connectionBadge")
        set_state(self.connection_status, state="checking")
        # Everything is permanent so temporary messages never overlap these labels.
        self.statusBar().addPermanentWidget(self.project_status)
        self.statusBar().addPermanentWidget(self.file_status)
        self.statusBar().addPermanentWidget(self.profile_status)
        self.statusBar().addPermanentWidget(self.cursor_status)
        self.statusBar().addPermanentWidget(self.connection_status)

        self.diagnostics = DiagnosticsPanel(server_url)
        self._syntax_check_file = ""
        self.syntax_checker = SyntaxChecker(self)
        self.syntax_checker.finished.connect(self._syntax_check_finished)
        self.syntax_checker.failed.connect(self._syntax_check_failed)
        self._show_cached_progress()
        self._create_actions()
        self._connect_signals()
        self._restore_window_state()
        self.connection_monitor = ConnectionMonitor(tutor_client, self)
        self.connection_monitor.start()

    def _restore_window_state(self) -> None:
        geometry = self.settings.value("window/geometry")
        state = self.settings.value("window/state")
        sizes = self.settings.value("window/splitter")
        if isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)
        if isinstance(state, QByteArray):
            self.restoreState(state)
        if isinstance(sizes, list):
            self.splitter.setSizes([int(size) for size in sizes])

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt API
        self.editor_tabs.write_recovery_drafts()
        if not self.editor_tabs.confirm_close_all():
            event.ignore()
            return
        self.settings.set_value("window/geometry", self.saveGeometry())
        self.settings.set_value("window/state", self.saveState())
        self.settings.set_value("window/splitter", self.splitter.sizes())
        self.connection_monitor.stop()
        event.accept()
