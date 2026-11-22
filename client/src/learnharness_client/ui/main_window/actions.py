"""Menus, signal wiring and the recent-projects menu."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QMessageBox

from learnharness_client.domain.project import Project, is_project_folder

from ...texts import T


class WindowActions:
    """Builds menus and connects signals."""

    def _create_actions(self) -> None:
        file_menu = self.menuBar().addMenu(T.MENU_FILE)
        open_project = QAction(T.OPEN_PROJECT, self)
        open_project.setShortcut(QKeySequence.StandardKey.Open)
        open_project.triggered.connect(self.pick_project)
        new_python = QAction(T.NEW_PYTHON_PROJECT, self)
        new_python.triggered.connect(self.create_python_project)
        open_python = QAction(T.OPEN_PYTHON_SCRIPT, self)
        open_python.triggered.connect(self.open_python_script)
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
        file_menu.addActions(
            [open_project, new_python, open_python, new_script, save, older_versions]
        )
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
        teacher_action = QAction(T.TEACHER_MENU, self)
        teacher_action.triggered.connect(self.show_teacher_area)
        edit_menu.addAction(teacher_action)

        view_menu = self.menuBar().addMenu(T.MENU_VIEW)
        problems_action = self.problems_dock.toggleViewAction()
        problems_action.setText(T.SHOW_PROBLEMS)
        view_menu.addAction(problems_action)

        check_menu = self.menuBar().addMenu(T.MENU_CHECK)
        syntax_action = QAction(T.SYNTAX_CHECK, self)
        self.syntax_action = syntax_action
        syntax_action.setShortcut(QKeySequence("F6"))
        syntax_action.triggered.connect(self.run_syntax_check)
        log_action = QAction(T.READ_GODOT_LOG, self)
        log_action.triggered.connect(self.read_godot_log)
        self.log_action = log_action
        check_menu.addActions([syntax_action, log_action])

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
        self.learn_agent_panel.exercise_submitted.connect(self._submit_agent_exercise)
        self.learn_agent_panel.show_changes_toggled.connect(self._set_show_changes)
        self.editor_tabs.generated_file_applied.connect(self._generated_file_applied)
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
        self.editor_tabs.explain_requested.connect(self.explain_selection)
        self.explain_panel.take_selection_requested.connect(self.explain_selection)
        self.explain_panel.question_asked.connect(self.ask_about_code)
        self.explain_panel.exercise_submitted.connect(self._submit_explain_exercise)
        self.project_panel.plan_requested.connect(self.request_project_plan)
        self.project_panel.plan_changed.connect(self._save_project_plan)
        self.mission_panel.mission_requested.connect(self.request_mission)
        self.mission_panel.step_requested.connect(self.request_mission_step)
        self.mission_panel.exercise_submitted.connect(self._submit_mission_exercise)
        self.mission_panel.progress_changed.connect(
            lambda state: self.settings.save_mission_progress(
                self.student_profile.profile_id, state
            )
        )
        self.mission_panel.mission_completed.connect(self._mission_completed)
        if self.admin_sync is not None:
            self.admin_sync.client.progress_received.connect(self._progress_received)
            # The copy on this PC first (offline), then the current list from the server.
            profile_id = self.student_profile.profile_id
            self.mission_panel.set_assigned(self.admin_sync.cached_missions(profile_id))
            self.admin_sync.fetch_missions(profile_id, self.mission_panel.set_assigned)

    def _refresh_recent_menu(self) -> None:
        self.recent_menu.clear()
        available = False
        for path_text in self.settings.recent_projects:
            path = Path(path_text)
            if not is_project_folder(path):
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
            self.open_project(Project.open(path))
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, T.PROJECT_NOT_OPENED, str(exc))
