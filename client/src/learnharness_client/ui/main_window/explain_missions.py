"""Requests of the tabs Code verstehen and Missionen."""

from __future__ import annotations

import logging

from learnharness_protocol import ReviewResult, StudentMessage, Submission

from ...texts import T
from .constants import is_target_file
from .scenes import ScenePlan

LOG = logging.getLogger(__name__)


class ExplainMissionActions:
    """Code explainer and missions."""

    def explain_selection(self) -> None:
        editor = self.editor_tabs.current_editor()
        relative = self._relative_current_file()
        self.learning_tabs.setCurrentWidget(self.explain_panel)
        if editor is None or relative is None:
            self.explain_panel.show_no_code()
            return
        code, start_line = editor.selected_or_nearby_text()
        self.explain_panel.set_code(relative, code[:16_000], start_line)

    def ask_about_code(self, question: str) -> None:
        if not self.project or not self.session_id:
            self.explain_panel.show_error(T.WAIT_FOR_SESSION)
            return
        self._response_owner = "explain"
        message = StudentMessage(
            intent="explain",
            language=self.project.language,
            **self._project_context(),
            session_id=self.session_id,
            project_id=self.project.project_id,
            experience_level=int(self.student_profile.experience_level),
            file=self.explain_panel.file,
            code_excerpt=self.explain_panel.code,
            excerpt_start_line=self.explain_panel.start_line,
            message=question,
        )
        self.tutor_client.send_message(message)

    def _submit_explain_exercise(self, submission: Submission) -> None:
        self._exercise_owner = "explain"
        self._submit_exercise(submission)

    def _mission_message(self, intent: str, text: str, **extra: object) -> StudentMessage | None:
        if not self.project or not self.session_id:
            self.mission_panel.show_error(T.WAIT_FOR_SESSION)
            return None
        relative = self._relative_current_file()
        if relative is None:
            self.mission_panel.show_error(T.MISSION_NEEDS_FILE)
            return None
        return StudentMessage(
            intent=intent,  # type: ignore[arg-type]
            language=self.project.language,
            **self._project_context(),
            session_id=self.session_id,
            project_id=self.project.project_id,
            experience_level=int(self.student_profile.experience_level),
            learning_level=None,
            file=relative,
            code_excerpt=self._current_file_text(),
            excerpt_start_line=1,
            message=text,
            **extra,
        )

    def request_mission(self, wish: str) -> None:
        message = self._mission_message("mission", wish)
        if message is not None:
            self._response_owner = "mission"
            self.tutor_client.send_message(message)

    def request_project_mission(self) -> None:
        message = self._mission_message(
            "mission", T.MISSION_PROJECT_WISH, mission_from_project=True
        )
        if message is not None:
            self._response_owner = "mission"
            self.tutor_client.send_message(message)

    def request_mission_step(self, mission_id: str, step_id: str) -> None:
        message = self._mission_message(
            "mission_step", step_id, mission_id=mission_id, mission_step_id=step_id
        )
        if message is None:
            return
        # Like the LearnAgent: generated code may only go into the file chosen for this step.
        self._mission_target_file = message.file
        self._mission_base_text = self._open_script_text()
        self._keep_scene_base()
        self._response_owner = "mission"
        self.tutor_client.send_message(message)

    def _mission_completed(self, mission_id: str) -> None:
        """Report missions the teacher assigned; free-wish missions stay on this PC."""
        if self.mission_panel.mission is not None:
            self.project_panel.add_finished_mission(self.mission_panel.mission.title)
        if self.admin_sync is None:
            return
        if not any(mission.id == mission_id for mission in self.mission_panel.assigned):
            return
        self.admin_sync.report_mission_done(
            self.student_profile.profile_id, mission_id, self.mission_panel.set_assigned
        )

    def _submit_mission_exercise(self, submission: Submission) -> None:
        self._exercise_owner = "mission"
        self._submit_exercise(submission)

    def _apply_mission_files(self, review: ReviewResult) -> None:
        written: list[str] = []
        scene_plan = self._plan_scene_edit(review)
        for generated in review.generated_files if scene_plan is not False else []:
            if not is_target_file(generated.path, self._mission_target_file):
                LOG.warning("Rejected generated file outside the mission target")
                continue
            if self.editor_tabs.apply_generated_file(
                generated.path, generated.content, self._mission_base_text
            ):
                written.append(generated.path)
        if written:
            self.statusBar().showMessage(T.AGENT_WROTE_FILE.format(file=", ".join(written)))
        if written and isinstance(scene_plan, ScenePlan):
            self._write_scene(scene_plan)
        self._mission_target_file = None
        self._mission_base_text = None
