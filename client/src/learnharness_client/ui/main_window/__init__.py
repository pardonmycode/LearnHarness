"""Main application window tying safe editing and tutoring together."""

from __future__ import annotations

import logging

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QDockWidget,
    QLabel,
    QMainWindow,
    QSplitter,
    QTabWidget,
)

from learnharness_client import design
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
from ..panels.terminal_panel import TerminalPanel
from ..panels.tutor_panel import TutorPanel
from ..script_tree import ScriptTree
from ..theme import set_state
from .actions import WindowActions
from .checks import CheckActions
from .constants import (
    GODOT_TASK_ID,
    MAX_FILE_CONTEXT,
    PYTHON_TASK_ID,
    is_target_file,
)
from .explain_missions import ExplainMissionActions
from .learning import LearningActions
from .project_flow import ProjectFlow
from .projects import ProjectActions
from .responses import ServerResponses
from .running import RunActions
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
    RunActions,
    ProjectFlow,
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
        self.resize(*design.MAIN_WINDOW_SIZE)

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
        learning_tabs.addTab(self.project_panel, T.TAB_PROJECT)
        learning_tabs.addTab(self.learn_agent_panel, T.TAB_AGENT)
        learning_tabs.addTab(self.mission_panel, T.TAB_MISSIONS)
        learning_tabs.addTab(self.explain_panel, T.TAB_EXPLAIN)
        learning_tabs.addTab(self.tutor_panel, T.TAB_TUTOR)
        learning_tabs.addTab(self.progress_panel, T.TAB_PROGRESS)
        self.learning_tabs = learning_tabs

        self.terminal = TerminalPanel(self._save_open_files, self._godot_program)
        code_splitter = QSplitter(Qt.Orientation.Horizontal)
        code_splitter.addWidget(self.script_tree)
        code_splitter.addWidget(self.editor_tabs)
        code_splitter.setStretchFactor(0, design.CODE_STRETCH[0])
        code_splitter.setStretchFactor(1, design.CODE_STRETCH[1])
        code_splitter.setChildrenCollapsible(False)
        code_splitter.setSizes(list(design.CODE_SPLIT))
        self.code_splitter = code_splitter
        # The terminal sits below tree and code; the learning tabs keep the full height.
        work_splitter = QSplitter(Qt.Orientation.Vertical)
        work_splitter.addWidget(code_splitter)
        work_splitter.addWidget(self.terminal)
        work_splitter.setStretchFactor(0, design.WORK_STRETCH[0])
        work_splitter.setStretchFactor(1, design.WORK_STRETCH[1])
        work_splitter.setChildrenCollapsible(False)
        work_splitter.setSizes(list(design.WORK_SPLIT))
        self.work_splitter = work_splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(work_splitter)
        splitter.addWidget(learning_tabs)
        splitter.setStretchFactor(0, design.MAIN_STRETCH[0])
        splitter.setStretchFactor(1, design.MAIN_STRETCH[1])
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(design.SPLITTER_HANDLE)
        learning_tabs.setMinimumWidth(design.LEARNING_TABS_MIN_WIDTH)
        work_splitter.setMinimumWidth(design.WORK_AREA_MIN_WIDTH)
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
        if isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)
        if isinstance(state, QByteArray):
            self.restoreState(state)
        for key, splitter in self._saved_splitters():
            sizes = self.settings.value(key)
            if isinstance(sizes, list) and len(sizes) == splitter.count():
                splitter.setSizes([int(size) for size in sizes])
            elif splitter is self.splitter:
                tabs = round(self.width() * design.LEARNING_TABS_SHARE)
                splitter.setSizes([self.width() - tabs, tabs])

    def _saved_splitters(self) -> tuple[tuple[str, QSplitter], ...]:
        return (
            ("window/main_splitter_v2", self.splitter),
            ("window/code_splitter", self.code_splitter),
            ("window/work_splitter", self.work_splitter),
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt API
        self.editor_tabs.write_recovery_drafts()
        if not self.editor_tabs.confirm_close_all():
            event.ignore()
            return
        self.terminal.shutdown()
        self.settings.set_value("window/geometry", self.saveGeometry())
        self.settings.set_value("window/state", self.saveState())
        for key, splitter in self._saved_splitters():
            self.settings.set_value(key, splitter.sizes())
        self.connection_monitor.stop()
        event.accept()
