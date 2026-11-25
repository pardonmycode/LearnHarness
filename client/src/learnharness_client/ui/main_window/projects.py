"""Opening and creating projects and scripts, and the project plan."""

from __future__ import annotations

from pathlib import Path

from learnharness_protocol import ProjectTurn, SessionInfo, StudentMessage
from PyQt6.QtWidgets import QInputDialog, QMessageBox

from learnharness_client.domain.project import Project
from learnharness_client.domain.project_plan import ProjectPlan

from ...texts import T
from ..project_picker import choose_project, choose_python_script, new_python_project
from .constants import GODOT_TASK_ID, MAX_FILE_CONTEXT, PYTHON_TASK_ID


class ProjectActions:
    """Project and script handling."""

    def pick_project(self) -> None:
        start = self.settings.recent_projects[0] if self.settings.recent_projects else ""
        project = choose_project(self, start, recent=self.settings.recent_projects)
        if project:
            self.open_project(project)

    def create_python_project(self) -> None:
        project = new_python_project(self)
        if project:
            self.open_project(project)

    def open_python_script(self) -> None:
        start = self.settings.recent_projects[0] if self.settings.recent_projects else ""
        chosen = choose_python_script(self, start)
        if chosen is None:
            return
        project, script = chosen
        if self.project is None or self.project.root != project.root:
            self.open_project(project)
        # Opening can be cancelled while unsaved changes of the old project are asked about.
        if self.project is not None and self.project.root == project.root:
            self.editor_tabs.open_file(script)

    def _apply_language(self, language: str) -> None:
        python = language == "python"
        self.current_task_id = PYTHON_TASK_ID if python else GODOT_TASK_ID
        self.syntax_action.setText(T.SYNTAX_CHECK_PYTHON if python else T.SYNTAX_CHECK)
        self.log_action.setEnabled(not python)
        self.problems_panel.set_language(language)
        self.mission_panel.set_language(language)
        self.project_panel.set_language(language)
        self.learn_agent_panel.prompt.setPlaceholderText(
            T.AGENT_WISH_PLACEHOLDER_PYTHON if python else T.AGENT_WISH_PLACEHOLDER
        )

    def open_project(self, project: Project) -> None:
        if self.project and not self.editor_tabs.confirm_close_all():
            return
        self.project = project
        self.terminal.set_project(project)
        self._apply_language(project.language)
        saved_plan = self.settings.project_plan(self.student_profile.profile_id, project.project_id)
        self.project_panel.load(ProjectPlan.from_dict(saved_plan))
        self._sync_project_idea()
        self._reset_project_hints()
        self.settings.remember_project(project.root)
        self._refresh_recent_menu()
        self.script_tree.set_project(project)
        self.editor_tabs.set_project(project)
        self._refresh_scene_view()
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
        prompt = (
            T.NEW_SCRIPT_PROMPT_PYTHON if self.project.language == "python" else T.NEW_SCRIPT_PROMPT
        )
        name, accepted = QInputDialog.getText(self, T.NEW_SCRIPT, prompt)
        if not accepted or not name.strip():
            return
        name = name.strip()
        suffix = ".py" if self.project.language == "python" else ".gd"
        if not name.casefold().endswith(suffix):
            name += suffix
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
        # The session's default task is a Godot task; Python projects keep their own.
        if session.current_task_id and (self.project is None or self.project.language != "python"):
            self.current_task_id = session.current_task_id
        self.tutor_client.fetch_progress()
        if self.admin_sync is not None:
            # The administration keeps the progress across PCs; it wins when it answers.
            self.admin_sync.fetch_progress(self.student_profile.profile_id)

    def _current_file_text(self) -> str | None:
        editor = self.editor_tabs.current_editor()
        text = editor.toPlainText() if editor is not None else ""
        return text[:MAX_FILE_CONTEXT] if text.strip() else None

    def _open_script_text(self) -> str:
        """The whole open script, to notice later whether it changed."""
        editor = self.editor_tabs.current_editor()
        return editor.toPlainText() if editor is not None else ""

    def _relative_current_file(self) -> str | None:
        document = self.editor_tabs.current_document()
        if document is None or self.project is None:
            return None
        return document.path.relative_to(self.project.root).as_posix()

    def request_project_plan(self, text: str) -> None:
        if not self.project or not self.session_id:
            self.project_panel.show_error(T.WAIT_FOR_SESSION)
            return
        plan = self.project_panel.plan
        self._response_owner = "project"
        self._plan_project_id = self.project.project_id
        message = StudentMessage(
            intent="project_plan",
            language=self.project.language,
            session_id=self.session_id,
            project_id=self.project.project_id,
            experience_level=int(self.student_profile.experience_level),
            **self._project_context(),
            project_question=self.project_panel.open_question,
            project_skipped_questions=self.project_panel.skipped_questions,
            project_turns=[
                ProjectTurn(question=turn.question, answer=turn.answer) for turn in plan.turns
            ],
            message=text,
        )
        self.tutor_client.send_message(message)

    def _save_project_plan(self, data: dict[str, object]) -> None:
        if self.project:
            self.settings.save_project_plan(
                self.student_profile.profile_id, self.project.project_id, data
            )
        self._sync_project_idea()
