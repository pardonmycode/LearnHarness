"""Main application window tying safe editing and tutoring together."""

from __future__ import annotations

import logging
from pathlib import Path

from learnharness_protocol import (
    HealthStatus,
    LearningResponse,
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
from learnharness_client.net.connection_monitor import ConnectionMonitor
from learnharness_client.net.tutor_client import ClientError, TutorClient

from .dialogs.settings_dialog import SettingsDialog
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
        self.active_learning_level = 1
        self.setWindowTitle("LearnHarness – Godot-Programmierwerkstatt")
        self.resize(1380, 840)

        self.script_tree = ScriptTree()
        self.editor_tabs = EditorTabs(settings)
        self.learn_agent_panel = LearnAgentPanel(
            settings.max_unlocked_learning_level(student_profile.profile_id)
        )
        self.tutor_panel = TutorPanel()
        self.progress_panel = ProgressPanel()

        learning_tabs = QTabWidget()
        learning_tabs.addTab(self.learn_agent_panel, "LearnAgent")
        learning_tabs.addTab(self.tutor_panel, "Tutor")
        learning_tabs.addTab(self.progress_panel, "Fortschritt")
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
        problems_dock = QDockWidget("Probleme und Godot-Fehler", self)
        problems_dock.setObjectName("problemsDock")
        problems_dock.setWidget(self.problems_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, problems_dock)
        problems_dock.setVisible(False)
        self.problems_dock = problems_dock

        self.project_status = QLabel("Kein Projekt geöffnet")
        self.file_status = QLabel("Keine Datei")
        self.profile_status = QLabel(
            f"Profil: {student_profile.pseudonym} · {student_profile.experience_label}"
        )
        self.cursor_status = QLabel("Zeile – · Spalte –")
        self.connection_status = QLabel("● Lernhelfer wird geprüft")
        self.connection_status.setObjectName("connectionBadge")
        set_state(self.connection_status, state="checking")
        # Everything is permanent so temporary messages never overlap these labels.
        self.statusBar().addPermanentWidget(self.project_status)
        self.statusBar().addPermanentWidget(self.file_status)
        self.statusBar().addPermanentWidget(self.profile_status)
        self.statusBar().addPermanentWidget(self.cursor_status)
        self.statusBar().addPermanentWidget(self.connection_status)

        self.diagnostics = DiagnosticsPanel(server_url)
        self._create_actions()
        self._connect_signals()
        self._restore_window_state()
        self.connection_monitor = ConnectionMonitor(tutor_client, self)
        self.connection_monitor.start()

    def _create_actions(self) -> None:
        file_menu = self.menuBar().addMenu("&Datei")
        open_project = QAction("Godot-Projekt öffnen …", self)
        open_project.setShortcut(QKeySequence.StandardKey.Open)
        open_project.triggered.connect(self.pick_project)
        new_script = QAction("Neues GDScript …", self)
        new_script.setShortcut(QKeySequence("Ctrl+Shift+N"))
        new_script.triggered.connect(self.create_script)
        save = QAction("Speichern", self)
        save.setShortcut(QKeySequence.StandardKey.Save)
        save.triggered.connect(self.editor_tabs.save_current)
        quit_action = QAction("Beenden", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addActions([open_project, new_script, save])
        self.recent_menu = file_menu.addMenu("Zuletzt verwendete Projekte")
        self._refresh_recent_menu()
        file_menu.addSeparator()
        file_menu.addAction(quit_action)

        edit_menu = self.menuBar().addMenu("&Bearbeiten")
        find_action = QAction("Suchen", self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.triggered.connect(lambda: self.editor_tabs.open_find(False))
        replace_action = QAction("Suchen und ersetzen", self)
        replace_action.setShortcut(QKeySequence.StandardKey.Replace)
        replace_action.triggered.connect(lambda: self.editor_tabs.open_find(True))
        goto_action = QAction("Gehe zu Zeile …", self)
        goto_action.setShortcut(QKeySequence("Ctrl+G"))
        goto_action.triggered.connect(self.goto_line)
        edit_menu.addActions([find_action, replace_action, goto_action])

        settings_action = QAction("Einstellungen …", self)
        settings_action.triggered.connect(self.show_settings)
        edit_menu.addSeparator()
        edit_menu.addAction(settings_action)

        view_menu = self.menuBar().addMenu("&Ansicht")
        problems_action = self.problems_dock.toggleViewAction()
        problems_action.setText("Probleme anzeigen")
        view_menu.addAction(problems_action)

        help_menu = self.menuBar().addMenu("&Hilfe")
        diagnostics_action = QAction("Technische Details", self)
        diagnostics_action.triggered.connect(self.show_diagnostics)
        help_menu.addAction(diagnostics_action)

    def _connect_signals(self) -> None:
        self.script_tree.file_open_requested.connect(self.editor_tabs.open_file)
        self.editor_tabs.status_message.connect(self.statusBar().showMessage)
        self.editor_tabs.current_file_changed.connect(self.file_status.setText)
        self.editor_tabs.cursor_changed.connect(
            lambda line, column: self.cursor_status.setText(f"Zeile {line} · Spalte {column}")
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
        self.tutor_client.progress_received.connect(self.progress_panel.set_progress)
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
        self.setWindowTitle(f"{project.name} – LearnHarness")
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
        self.statusBar().showMessage(
            "Projekt geöffnet. Du kannst auch ohne Lernserver arbeiten.", 5000
        )

    def create_script(self) -> None:
        if not self.project:
            QMessageBox.information(self, "Erst Projekt öffnen", "Öffne zuerst ein Godot-Projekt.")
            return
        name, accepted = QInputDialog.getText(
            self, "Neues GDScript", "Dateiname, zum Beispiel enemy.gd:"
        )
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
        line, accepted = QInputDialog.getInt(self, "Gehe zu Zeile", "Zeilennummer:", 1, 1, maximum)
        if accepted:
            self.editor_tabs.goto_line(line)

    def _session_started(self, session: SessionInfo) -> None:
        self.session_id = session.session_id
        if session.current_task_id:
            self.current_task_id = session.current_task_id
        self.tutor_client.fetch_progress()

    def start_learning_round(self, prompt: str, level: int) -> None:
        if not self.project or not self.session_id:
            self.learn_agent_panel.show_error(
                "Öffne zuerst ein Projekt und warte kurz auf den Lernserver."
            )
            return
        document = self.editor_tabs.current_document()
        if document is None:
            self.learn_agent_panel.show_error(
                "Öffne zuerst die GDScript-Datei, die der LearnAgent später schreiben soll."
            )
            return
        self.learn_round_active = True
        self._awaiting_learn_response = True
        self.active_learning_level = level
        relative = document.path.relative_to(self.project.root).as_posix()
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
            self.tutor_panel.show_error("Öffne zuerst ein Projekt und warte kurz auf die Sitzung.")
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
                self.problems_panel.add_problem(Problem(relative, line, review.feedback, "Prüfung"))

    def _health_changed(self, health: HealthStatus) -> None:
        self._set_online(health.server_ok and health.model_ok)
        self.diagnostics.set_health(health)

    def _set_online(self, online: bool) -> None:
        self.connection_status.setText(
            "● Der Lernhelfer ist da" if online else "● Der Lernhelfer macht Pause"
        )
        self.connection_status.setToolTip(
            "Du kannst Fragen stellen."
            if online
            else "Du kannst trotzdem weiter programmieren und speichern."
        )
        set_state(self.connection_status, state="online" if online else "offline")

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
        dialog.setWindowTitle("Technische Details")
        dialog.resize(560, 300)
        layout = QHBoxLayout(dialog)
        panel = DiagnosticsPanel(self.server_url)
        panel.server.setText(self.diagnostics.server.text())
        panel.model.setText(self.diagnostics.model.text())
        panel.latency.setText(self.diagnostics.latency.text())
        panel.last_error.setText(self.diagnostics.last_error.text())
        layout.addWidget(panel)
        dialog.exec()

    def show_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            QMessageBox.information(
                self,
                "Einstellungen gespeichert",
                "Die neuen Netzwerk- und Anzeigeeinstellungen gelten beim nächsten Start.",
            )

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
            QMessageBox.warning(self, "Projekt nicht geöffnet", str(exc))

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
