"""LearnAgent rounds, tutor messages and exercise reviews."""

from __future__ import annotations

import logging

from learnharness_protocol import ReviewResult, StudentMessage, Submission

from ...texts import T
from ..panels.problems_panel import Problem
from .constants import is_target_file
from .scenes import ScenePlan

LOG = logging.getLogger(__name__)


class LearningActions:
    """LearnAgent and tutor."""

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
        self._learn_base_text = self._open_script_text()
        message = StudentMessage(
            intent="learn",
            language=self.project.language,
            **self._project_context(),
            session_id=self.session_id,
            project_id=self.project.project_id,
            experience_level=int(self.student_profile.experience_level),
            learning_level=level,
            current_task=f"learn_level_{level}",
            file=relative,
            # The whole file, so the server can release a small, explained change of it.
            code_excerpt=self._current_file_text(),
            excerpt_start_line=1,
            skill_focus=self.learn_agent_panel.current_focus,
            message=prompt,
        )
        self._keep_scene_base()
        self.tutor_client.send_message(message)

    def send_tutor_message(self, text: str, *, hint_level: int | None = None) -> None:
        if not self.project or not self.session_id:
            self.tutor_panel.show_error(T.WAIT_FOR_SESSION)
            return
        if hint_level is None:
            self._reset_project_hints()  # a new question starts its hints from the beginning
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
            self.tutor_panel.set_context_description(
                relative,
                start_line,
                end_line,
                with_idea=bool(self.project_panel.plan.description.strip()),
            )
        message = StudentMessage(
            language=self.project.language,
            **self._project_context(),
            session_id=self.session_id,
            project_id=self.project.project_id,
            experience_level=int(self.student_profile.experience_level),
            current_task=self.current_task_id,
            file=relative,
            code_excerpt=excerpt,
            excerpt_start_line=start_line,
            last_error=self._latest_error(),
            project_hint_level=hint_level,
            message=text,
        )
        self.tutor_client.send_message(message)

    def request_code_review(self) -> None:
        """Feedback on the whole open script; it changes nothing in the file."""
        if not self.project or not self.session_id:
            self.tutor_panel.show_error(T.WAIT_FOR_SESSION)
            return
        relative = self._relative_current_file()
        code = self._current_file_text()
        if relative is None or code is None:
            self.tutor_panel.show_error(T.TUTOR_REVIEW_NEEDS_FILE)
            return
        text = T.TUTOR_REVIEW_REQUEST.format(file=relative)
        self.tutor_panel.show_request(text)
        self.tutor_panel.set_waiting()
        self._review_file = relative
        self.tutor_client.send_message(
            StudentMessage(
                intent="review",
                language=self.project.language,
                **self._project_context(),
                session_id=self.session_id,
                project_id=self.project.project_id,
                experience_level=int(self.student_profile.experience_level),
                current_task=self.current_task_id,
                file=relative,
                code_excerpt=code,
                excerpt_start_line=1,
                last_error=self._latest_error(),
                message=text,
            )
        )

    def _show_review_lines(self, lines: list[int]) -> None:
        """Marks the lines only while the reviewed script is still the open one."""
        editor = self.editor_tabs.current_editor()
        if editor is not None and self._relative_current_file() == self._review_file:
            editor.set_error_lines(lines)

    def _submit_agent_exercise(self, submission: Submission) -> None:
        self._exercise_owner = "agent"
        self._submit_exercise(submission)

    def _submit_exercise(self, submission: Submission) -> None:
        # The server needs the session to know which LearnAgent round is being answered.
        if self.session_id and submission.session_id is None:
            submission = submission.model_copy(update={"session_id": self.session_id})
        self.tutor_client.submit_exercise(submission)

    def _exercise_received(self, exercise) -> None:
        self._exercise_owner = "agent"
        self.learn_agent_panel.show_exercise(exercise)
        self.learning_tabs.setCurrentWidget(self.learn_agent_panel)

    def _review_received(self, review: ReviewResult) -> None:
        if self._exercise_owner == "explain":
            if review.generated_files:
                LOG.warning("Ignored generated files for a code explanation")
            self.explain_panel.show_review(review)
            return
        if self._exercise_owner == "mission":
            self.mission_panel.show_review(review)
            if review.correct and review.generated_files:
                self._apply_mission_files(review)
            return
        self.learn_agent_panel.show_review(review)
        written_files: list[str] = []
        explanations: list[str] = []
        if review.generated_files and not self.learn_round_active:
            LOG.warning("Ignored generated files outside an active LearnAgent round")
        scene_plan = self._plan_scene_edit(review) if review.correct else None
        if review.correct and self.learn_round_active and scene_plan is not False:
            for generated in review.generated_files:
                if not self._is_learn_target(generated.path):
                    # The agent may only write the file the child chose for this round.
                    LOG.warning("Rejected generated file outside the active LearnAgent target")
                    continue
                if self.editor_tabs.apply_generated_file(
                    generated.path, generated.content, self._learn_base_text
                ):
                    written_files.append(generated.path)
                    explanations.append(generated.explanation)
            code_written = len(written_files)
            wrote_scene = (
                bool(written_files)
                and isinstance(scene_plan, ScenePlan)
                and self._write_scene(scene_plan)
            )
            if wrote_scene and isinstance(scene_plan, ScenePlan):
                written_files.append(scene_plan.relative)
                explanations.append(T.SCENE_WRITTEN.format(file=scene_plan.relative))
            if review.generated_files:
                self.learn_agent_panel.show_code_result(written_files, explanations)
            if code_written and code_written == len(review.generated_files):
                unlocked = self.settings.unlock_learning_level(
                    self.student_profile.profile_id,
                    min(10, self.active_learning_level + 1),
                )
                self.learn_agent_panel.set_max_unlocked(unlocked)
                if self.admin_sync is not None:
                    self.admin_sync.unlock(
                        self.student_profile.profile_id,
                        unlocked,
                        self.learn_agent_panel.set_max_unlocked,
                    )
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
        return is_target_file(path, self._learn_target_file)
