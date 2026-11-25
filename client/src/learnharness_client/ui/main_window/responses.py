"""Answers, connection state and progress from the learning server."""

from __future__ import annotations

import logging

from learnharness_protocol import HealthStatus, LearningResponse, ProgressUpdate

from learnharness_client.net.tutor_client import ClientError

from ...texts import T
from ..theme import set_state

LOG = logging.getLogger(__name__)


class ServerResponses:
    """Reacts to the tutor client."""

    def _stream_started(self) -> None:
        if self._response_owner == "explain":
            self.explain_panel.begin_stream()
        elif not self._awaiting_learn_response and self._response_owner is None:
            self.tutor_panel.begin_stream()

    def _stream_chunk(self, text: str) -> None:
        if self._response_owner == "explain":
            self.explain_panel.append_stream_chunk(text)
        elif not self._awaiting_learn_response and self._response_owner is None:
            self.tutor_panel.append_stream_chunk(text)

    def _learning_response(self, response: LearningResponse) -> None:
        owner, self._response_owner = self._response_owner, None
        if owner == "explain":
            self.explain_panel.show_response(response)
            return
        if owner == "mission":
            self._show_scene_preview(response.scene_preview)
            self.mission_panel.show_step_response(response)
            return
        if owner == "project":
            # An answer for a project that was closed meanwhile must not land in this plan.
            if self.project and self._plan_project_id == self.project.project_id:
                self.project_panel.show_response(response)
            return
        if self._awaiting_learn_response:
            # LearnAgent answers belong in the LearnAgent tab, not in the tutor chat.
            self._awaiting_learn_response = False
            self._show_scene_preview(response.scene_preview)
            self.learn_agent_panel.show_response(response)
            return
        self.tutor_panel.finish_stream(response)
        self._hint_answered()
        if response.mode == "review":
            self._show_review_lines(response.marked_lines)
        if response.exercise is not None:
            self._exercise_received(response.exercise)

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
        self.explain_panel.set_available(online)
        self.mission_panel.set_available(online)
        self.project_panel.set_available(online)

    def _client_error(self, error: ClientError) -> None:
        owner, self._response_owner = self._response_owner, None
        self._pending_hint = None  # the same hint can be asked for again
        if owner == "explain":
            self.explain_panel.show_error(error.message_for_child)
        elif owner == "mission":
            self.mission_panel.show_error(error.message_for_child)
        elif owner == "project":
            self.project_panel.show_error(error.message_for_child)
        self.tutor_panel.show_error(error.message_for_child)
        if self.learn_round_active:
            self.learn_agent_panel.show_error(error.message_for_child)
            self.learn_round_active = False
            self._awaiting_learn_response = False
        self.diagnostics.set_error(error.technical_code)
        if error.technical_code in {"network_error", "socket"}:
            self._set_online(False)

    def _progress_received(self, progress: ProgressUpdate) -> None:
        self.progress_panel.set_progress(progress)
        self.learn_agent_panel.set_skills(progress.skills)
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
        self.learn_agent_panel.set_skills(progress.skills)
