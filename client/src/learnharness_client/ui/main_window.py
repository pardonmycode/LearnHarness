"""Main application window tying safe editing and tutoring together."""

from __future__ import annotations

import logging
from pathlib import Path, PurePosixPath

from learnharness_protocol import (
    HealthStatus,
    LearningResponse,
    ProgressUpdate,
    ReviewResult,
    SessionInfo,
    StudentMessage,
    Submission,
)
from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import (
    QDialog,
    QDockWidget,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTabWidget,
)

from learnharness_client.config import AppSettings
from learnharness_client.domain.profile import StudentProfile
from learnharness_client.domain.project import GodotProject
from learnharness_client.godot.log_reader import default_log_path, read_recent_errors
from learnharness_client.godot.output_parser import GodotMessage
from learnharness_client.godot.syntax_check import SyntaxChecker
from learnharness_client.net.connection_monitor import ConnectionMonitor
from learnharness_client.net.tutor_client import ClientError, TutorClient

from ..texts import T
from .dialogs.backup_dialog import BackupDialog
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.tutorial_dialog import TutorialDialog
from .editor.editor_tabs import EditorTabs
from .panels.diagnostics_panel import DiagnosticsPanel
from .panels.learn_agent_panel import LearnAgentPanel
from .panels.problems_panel import Problem, ProblemsPanel
from .panels.progress_panel import ProgressPanel
from .panels.tutor_panel import TutorPanel
from .project_picker import choose_project
from .script_tree import ScriptTree
from .theme import set_state

LOG = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(
        self,
        settings: AppSettings,
        tutor_client: TutorClient,
        student_profile: StudentProfile,
        *,
        server_url: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.settings = settings
        self.tutor_client = tutor_client
        self.student_profile = student_profile
        self.server_url = server_url
        self.project: GodotProject | None = None
        self.session_id: str | None = None
        self.current_task_id = "move_player_right"
        self.learn_round_active = False
        self._awaiting_learn_response = False
        self._learn_target_file: str | None = None
        self.active_learning_level = 1
        self.setWindowTitle(T.APP_TITLE)
        self.resize(1380, 840)

        self.script_tree = ScriptTree()
        self.editor_tabs = EditorTabs(settings)
        self.learn_agent_panel = LearnAgentPanel(
            settings.max_unlocked_learning_level(student_profile.profile_id)
        )
        self.tutor_panel = TutorPanel()
        self.progress_panel = ProgressPanel()

        learning_tabs = QTabWidget()
        learning_tabs.addTab(self.learn_agent_panel, T.TAB_AGENT)
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

    def _create_actions(self) -> None:
        file_menu = self.menuBar().addMenu(T.MENU_FILE)
        open_project = QAction(T.OPEN_PROJECT, self)
        open_project.setShortcut(QKeySequence.StandardKey.Open)
        open_project.triggered.connect(self.pick_project)
        new_script = QAction(T.NEW_SCRIPT, self)
        new_script.setShortcut(QKeySequence("Ctrl+Shift+N"))
        new_script.triggered.connect(self.create_script)
        save = QAction(T.SAVE, self)
        save.setShortcut(QKeySequence.StandardKey.Save)
        save.triggered.connect(self.editor_tabs.save_current)
        quit_action = QAction(T.QUIT, self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        older_versions = QAction(T.OLDER_VERSIONS, self)
        older_versions.triggered.connect(self.show_older_versions)
        file_menu.addActions([open_project, new_script, save, older_versions])
        self.recent_menu = file_menu.addMenu(T.RECENT_PROJECTS)
        self._refresh_recent_menu()
        file_menu.addSeparator()
        file_menu.addAction(quit_action)

        edit_menu = self.menuBar().addMenu(T.MENU_EDIT)
        find_action = QAction(T.FIND, self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.triggered.connect(lambda: self.editor_tabs.open_find(False))
        replace_action = QAction(T.REPLACE, self)
        replace_action.setShortcut(QKeySequence.StandardKey.Replace)
        replace_action.triggered.connect(lambda: self.editor_tabs.open_find(True))
        goto_action = QAction(T.GOTO_LINE, self)
        goto_action.setShortcut(QKeySequence("Ctrl+G"))
        goto_action.triggered.connect(self.goto_line)
        edit_menu.addActions([find_action, replace_action, goto_action])

        settings_action = QAction(T.SETTINGS, self)
        settings_action.triggered.connect(self.show_settings)
        edit_menu.addSeparator()
        edit_menu.addAction(settings_action)

        view_menu = self.menuBar().addMenu(T.MENU_VIEW)
        problems_action = self.problems_dock.toggleViewAction()
        problems_action.setText(T.SHOW_PROBLEMS)
        view_menu.addAction(problems_action)

        godot_menu = self.menuBar().addMenu(T.MENU_GODOT)
        syntax_action = QAction(T.SYNTAX_CHECK, self)
        syntax_action.setShortcut(QKeySequence("F6"))
        syntax_action.triggered.connect(self.run_syntax_check)
        log_action = QAction(T.READ_GODOT_LOG, self)
        log_action.triggered.connect(self.read_godot_log)
        godot_menu.addActions([syntax_action, log_action])

        help_menu = self.menuBar().addMenu(T.MENU_HELP)
        tutorial_action = QAction(T.TUTORIAL, self)
        tutorial_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        tutorial_action.triggered.connect(self.show_tutorial)
        diagnostics_action = QAction(T.DIAGNOSTICS, self)
        diagnostics_action.triggered.connect(self.show_diagnostics)
        help_menu.addActions([tutorial_action, diagnostics_action])

    def _connect_signals(self) -> None:
        self.script_tree.file_open_requested.connect(self.editor_tabs.open_file)
        self.editor_tabs.status_message.connect(self.statusBar().showMessage)
        self.editor_tabs.current_file_changed.connect(self.file_status.setText)
        self.editor_tabs.cursor_changed.connect(
            lambda line, column: self.cursor_status.setText(
                T.CURSOR.format(line=line, column=column)
            )
        )
        self.learn_agent_panel.start_requested.connect(self.start_learning_round)
        self.learn_agent_panel.exercise_submitted.connect(self._submit_exercise)
        self.tutor_panel.message_submitted.connect(self.send_tutor_message)
        self.tutor_panel.next_hint_requested.connect(
            lambda: self.tutor_client.request_next_hint(self.current_task_id)
        )
        self.tutor_panel.cancel_requested.connect(self.tutor_client.cancel)
        self.problems_panel.problem_activated.connect(self.open_problem)

        self.tutor_client.health_changed.connect(self._health_changed)
        self.tutor_client.session_started.connect(self._session_started)
        self.tutor_client.stream_started.connect(self._stream_started)
        self.tutor_client.stream_chunk.connect(self._stream_chunk)
        self.tutor_client.stream_finished.connect(self._learning_response)
        self.tutor_client.exercise_received.connect(self._exercise_received)
        self.tutor_client.review_received.connect(self._review_received)
        self.tutor_client.progress_received.connect(self._progress_received)
        self.tutor_client.error.connect(self._client_error)

    def pick_project(self) -> None:
        start = self.settings.recent_projects[0] if self.settings.recent_projects else ""
        project = choose_project(self, start)
        if project:
            self.open_project(project)

    def open_project(self, project: GodotProject) -> None:
        if self.project and not self.editor_tabs.confirm_close_all():
            return
        self.project = project
        self.settings.remember_project(project.root)
        self._refresh_recent_menu()
        self.script_tree.set_project(project)
        self.editor_tabs.set_project(project)
        self.project_status.setText(project.name)
        self.setWindowTitle(T.PROJECT_TITLE.format(project=project.name))
        self.session_id = None
        self.tutor_client.start_session(
            project.project_id,
            self.student_profile.profile_id,
            self.student_profile.pseudonym,
            int(self.student_profile.experience_level),
        )
        scripts = project.guard.iter_scripts()
        if scripts:
            self.editor_tabs.open_file(scripts[0])
        self.statusBar().showMessage(T.PROJECT_OPENED, 5000)

    def create_script(self) -> None:
        if not self.project:
            QMessageBox.information(self, T.OPEN_PROJECT_FIRST_TITLE, T.OPEN_PROJECT_FIRST)
            return
        name, accepted = QInputDialog.getText(self, T.NEW_SCRIPT, T.NEW_SCRIPT_PROMPT)
        if not accepted or not name.strip():
            return
        name = name.strip()
        if not name.casefold().endswith(".gd"):
            name += ".gd"
        editor = self.editor_tabs.create_file(Path(name))
        if editor:
            self.script_tree.refresh()

    def goto_line(self) -> None:
        editor = self.editor_tabs.current_editor()
        maximum = editor.blockCount() if editor else 1
        line, accepted = QInputDialog.getInt(self, T.GOTO_LINE, T.GOTO_LINE_PROMPT, 1, 1, maximum)
        if accepted:
            self.editor_tabs.goto_line(line)

    def _session_started(self, session: SessionInfo) -> None:
        self.session_id = session.session_id
        self.diagnostics.set_session(session.session_id)
        if session.current_task_id:
            self.current_task_id = session.current_task_id
        self.tutor_client.fetch_progress()

    def start_learning_round(self, prompt: str, level: int) -> None:
        if not self.project or not self.session_id:
            self.learn_agent_panel.show_error(T.WAIT_FOR_SESSION)
            return
        document = self.editor_tabs.current_document()
        if document is None:
            self.learn_agent_panel.show_error(T.AGENT_NEEDS_FILE)
            return
        self.learn_round_active = True
        self._awaiting_learn_response = True
        self.active_learning_level = level
        relative = document.path.relative_to(self.project.root).as_posix()
        self._learn_target_file = relative
        message = StudentMessage(
            session_id=self.session_id,
            project_id=self.project.project_id,
            experience_level=int(self.student_profile.experience_level),
            learning_level=level,
            current_task=f"learn_level_{level}",
            file=relative,
            message=prompt,
        )
        self.tutor_client.send_message(message)

    def send_tutor_message(self, text: str) -> None:
        if not self.project or not self.session_id:
            self.tutor_panel.show_error(T.WAIT_FOR_SESSION)
            return
        document = self.editor_tabs.current_document()
        editor = self.editor_tabs.current_editor()
        excerpt: str | None = None
        start_line: int | None = None
        relative: str | None = None
        if document and editor:
            excerpt, start_line = editor.selected_or_nearby_text()
            excerpt = excerpt[:16_000]
            relative = document.path.relative_to(self.project.root).as_posix()
            end_line = start_line + max(0, excerpt.count("\n"))
            self.tutor_panel.set_context_description(relative, start_line, end_line)
        message = StudentMessage(
            session_id=self.session_id,
            project_id=self.project.project_id,
            experience_level=int(self.student_profile.experience_level),
            current_task=self.current_task_id,
            file=relative,
            code_excerpt=excerpt,
            excerpt_start_line=start_line,
            last_error=self.problems_panel.last_error(),
            message=text,
        )
        self.tutor_client.send_message(message)

    def _submit_exercise(self, submission: Submission) -> None:
        # The server needs the session to know which LearnAgent round is being answered.
        if self.session_id and submission.session_id is None:
            submission = submission.model_copy(update={"session_id": self.session_id})
        self.tutor_client.submit_exercise(submission)

    def _stream_started(self) -> None:
        if not self._awaiting_learn_response:
            self.tutor_panel.begin_stream()

    def _stream_chunk(self, text: str) -> None:
        if not self._awaiting_learn_response:
            self.tutor_panel.append_stream_chunk(text)

    def _learning_response(self, response: LearningResponse) -> None:
        if self._awaiting_learn_response:
            # LearnAgent answers belong in the LearnAgent tab, not in the tutor chat.
            self._awaiting_learn_response = False
            self.learn_agent_panel.show_response(response)
            return
        self.tutor_panel.finish_stream(response)
        if response.exercise is not None:
            self._exercise_received(response.exercise)

    def _exercise_received(self, exercise) -> None:
        self.learn_agent_panel.show_exercise(exercise)
        self.learning_tabs.setCurrentWidget(self.learn_agent_panel)

    def _review_received(self, review: ReviewResult) -> None:
        self.learn_agent_panel.show_review(review)
        written_files: list[str] = []
        explanations: list[str] = []
        if review.generated_files and not self.learn_round_active:
            LOG.warning("Ignored generated files outside an active LearnAgent round")
        if review.correct and self.learn_round_active:
            for generated in review.generated_files:
                if not self._is_learn_target(generated.path):
                    # The agent may only write the file the child chose for this round.
                    LOG.warning("Rejected generated file outside the active LearnAgent target")
                    continue
                if self.editor_tabs.apply_generated_file(generated.path, generated.content):
                    written_files.append(generated.path)
                    explanations.append(generated.explanation)
            if review.generated_files:
                self.learn_agent_panel.show_code_result(written_files, explanations)
            if written_files and len(written_files) == len(review.generated_files):
                unlocked = self.settings.unlock_learning_level(
                    self.student_profile.profile_id,
                    min(10, self.active_learning_level + 1),
                )
                self.learn_agent_panel.set_max_unlocked(unlocked)
            self.learn_round_active = False
        editor = self.editor_tabs.current_editor()
        if editor:
            editor.set_error_lines(review.marked_lines)
        document = self.editor_tabs.current_document()
        if document and self.project:
            relative = document.path.relative_to(self.project.root).as_posix()
            for line in review.marked_lines:
                self.problems_panel.add_problem(
                    Problem(relative, line, review.feedback, T.SOURCE_REVIEW)
                )

    def _is_learn_target(self, path: str) -> bool:
        if self._learn_target_file is None:
            return False
        normalized = PurePosixPath(path.replace("\\", "/")).as_posix().removeprefix("./")
        return normalized.casefold() == self._learn_target_file.casefold()

    def _health_changed(self, health: HealthStatus) -> None:
        self._set_online(health.server_ok and health.model_ok)
        self.diagnostics.set_health(health)

    def _set_online(self, online: bool) -> None:
        self.connection_status.setText(T.CONNECTION_ONLINE if online else T.CONNECTION_OFFLINE)
        self.connection_status.setToolTip(
            T.CONNECTION_ONLINE_TIP if online else T.CONNECTION_OFFLINE_TIP
        )
        set_state(self.connection_status, state="online" if online else "offline")
        self.tutor_panel.set_available(online)
        self.learn_agent_panel.set_available(online)

    def _client_error(self, error: ClientError) -> None:
        self.tutor_panel.show_error(error.message_for_child)
        if self.learn_round_active:
            self.learn_agent_panel.show_error(error.message_for_child)
            self.learn_round_active = False
            self._awaiting_learn_response = False
        self.diagnostics.set_error(error.technical_code)
        if error.technical_code in {"network_error", "socket"}:
            self._set_online(False)

    def open_relative_file(self, relative: str) -> None:
        if self.project:
            self.editor_tabs.open_file(self.project.root / relative)

    def open_problem(self, relative: str, line: int) -> None:
        self.open_relative_file(relative)
        self.editor_tabs.goto_line(line)

    def show_diagnostics(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(T.DIAGNOSTICS)
        dialog.resize(560, 300)
        layout = QHBoxLayout(dialog)
        panel = DiagnosticsPanel(self.server_url)
        panel.server.setText(self.diagnostics.server.text())
        panel.model.setText(self.diagnostics.model.text())
        panel.session.setText(self.diagnostics.session.text())
        panel.latency.setText(self.diagnostics.latency.text())
        panel.last_error.setText(self.diagnostics.last_error.text())
        layout.addWidget(panel)
        dialog.exec()

    def show_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            QMessageBox.information(self, T.SETTINGS_SAVED_TITLE, T.SETTINGS_SAVED)

    def _progress_received(self, progress: ProgressUpdate) -> None:
        self.progress_panel.set_progress(progress)
        self.settings.cache_progress(self.student_profile.profile_id, progress.model_dump_json())

    def _show_cached_progress(self) -> None:
        raw = self.settings.cached_progress(self.student_profile.profile_id)
        if not raw:
            return
        try:
            progress = ProgressUpdate.model_validate_json(raw)
        except ValueError:
            LOG.warning("Ignored invalid cached progress")
            return
        self.progress_panel.set_progress(progress, cached=True)

    def show_older_versions(self) -> None:
        document = self.editor_tabs.current_document()
        if document is None:
            QMessageBox.information(self, T.OLDER_VERSIONS, T.OPEN_FILE_FIRST)
            return
        backups = self.editor_tabs.backups_for_current()
        if not backups:
            QMessageBox.information(
                self, T.OLDER_VERSIONS, T.NO_BACKUPS.format(file=document.path.name)
            )
            return
        dialog = BackupDialog(document.path.name, backups, self)
        if (
            dialog.exec()
            and dialog.restored_text is not None
            and self.editor_tabs.restore_into_current(dialog.restored_text)
        ):
            self.statusBar().showMessage(T.VERSION_RESTORED.format(file=document.path.name), 8000)

    def show_tutorial(self) -> None:
        TutorialDialog(self).exec()
        self.settings.mark_tutorial_seen(self.student_profile.profile_id)

    def show_tutorial_once(self) -> None:
        if not self.settings.tutorial_seen(self.student_profile.profile_id):
            self.show_tutorial()

    def run_syntax_check(self) -> None:
        document = self.editor_tabs.current_document()
        if not self.project or document is None:
            QMessageBox.information(self, T.SYNTAX_CHECK, T.OPEN_FILE_FIRST)
            return
        if not self.settings.godot_path:
            QMessageBox.information(self, T.SYNTAX_CHECK, T.GODOT_NOT_SET)
            return
        # Godot reads the file from disk, so it must see the same state as the editor.
        if document.dirty and not self.editor_tabs.save_current():
            return
        self._syntax_check_file = document.path.relative_to(self.project.root).as_posix()
        if self.syntax_checker.start(self.settings.godot_path, self.project.root, document.path):
            self.statusBar().showMessage(
                T.GODOT_CHECK_RUNNING.format(file=document.path.name), 10_000
            )

    def _syntax_check_finished(self, messages: list[GodotMessage]) -> None:
        file = self._syntax_check_file
        self.problems_panel.clear_source(T.SOURCE_GODOT_CHECK)
        editor = self.editor_tabs.current_editor()
        if editor:
            editor.set_error_lines(
                [m.line for m in messages if m.file.casefold() == file.casefold()]
            )
        if not messages:
            self.statusBar().showMessage(T.GODOT_CHECK_OK.format(file=file), 8000)
            return
        self._add_godot_messages(messages, T.SOURCE_GODOT_CHECK)
        self.statusBar().showMessage(T.GODOT_CHECK_ERRORS.format(count=len(messages)), 8000)

    def _syntax_check_failed(self, reason: str) -> None:
        self.statusBar().showMessage(T.GODOT_CHECK_FAILED.format(reason=reason), 8000)

    def read_godot_log(self) -> None:
        if not self.project:
            QMessageBox.information(self, T.READ_GODOT_LOG, T.OPEN_PROJECT_FIRST)
            return
        log_path = default_log_path(self.project.name)
        if log_path is None or not log_path.is_file():
            QMessageBox.information(self, T.READ_GODOT_LOG, T.GODOT_LOG_MISSING)
            return
        try:
            messages = read_recent_errors(log_path)
        except OSError as exc:
            QMessageBox.warning(self, T.READ_GODOT_LOG, str(exc))
            return
        added = self._add_godot_messages(messages, T.SOURCE_GODOT_LOG)
        text = T.GODOT_LOG_FOUND.format(count=added) if added else T.GODOT_LOG_EMPTY
        self.statusBar().showMessage(text, 8000)

    def _add_godot_messages(self, messages: list[GodotMessage], source: str) -> int:
        added = 0
        for message in messages:
            problem = Problem(message.file, message.line, message.message, source)
            if self.problems_panel.add_problem(problem):
                added += 1
        if added:
            self.problems_dock.setVisible(True)
        return added

    def _refresh_recent_menu(self) -> None:
        self.recent_menu.clear()
        available = False
        for path_text in self.settings.recent_projects:
            path = Path(path_text)
            if not (path / "project.godot").is_file():
                continue
            available = True
            action = self.recent_menu.addAction(path.name)
            action.setToolTip(str(path))
            action.triggered.connect(
                lambda _checked=False, current=path: self._open_recent(current)
            )
        self.recent_menu.setEnabled(available)

    def _open_recent(self, path: Path) -> None:
        try:
            self.open_project(GodotProject.open(path))
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, T.PROJECT_NOT_OPENED, str(exc))

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
