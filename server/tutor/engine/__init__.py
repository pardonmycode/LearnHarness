"""What the learning server does for each request; every AI call goes through the harness."""

from __future__ import annotations

import logging
from collections.abc import Callable

from django.utils import timezone
from learnharness_protocol import StudentMessage

from ..models import AiSettings, TutorSession
from ..providers import Provider, ProviderError, get_provider
from .ai_calls import AiCalls
from .missions import TutorMissions
from .reviews import TutorReviews
from .rounds import TutorRounds
from .tasks import (
    HISTORY_TURNS,
    TASK_LANGUAGES,
    TASK_SKILLS,
    TASKS,
    TOO_FAST,
    UNAVAILABLE,
    Response,
    _error,
)

__all__ = [
    "HISTORY_TURNS",
    "LOG",
    "Response",
    "TASKS",
    "TASK_LANGUAGES",
    "TASK_SKILLS",
    "TOO_FAST",
    "Tutor",
    "UNAVAILABLE",
]


LOG = logging.getLogger(__name__)


class Tutor(AiCalls, TutorRounds, TutorMissions, TutorReviews):
    def __init__(
        self,
        session: TutorSession,
        settings: AiSettings | None = None,
        provider: Provider | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or AiSettings.load()
        self._provider = provider

    @property
    def provider(self) -> Provider:
        if self._provider is None:
            self._provider = get_provider(self.settings)
        return self._provider

    def handle(
        self, message: StudentMessage, on_chunk: Callable[[str], None] | None = None
    ) -> Response:
        self.session.last_activity = timezone.now()
        self.session.save(update_fields=["last_activity"])
        if self._rate_limited():
            return _error("rate_limited", TOO_FAST, retry_after=30)
        handlers: dict[str, Callable[[StudentMessage], Response]] = {
            "learn": self._learn,
            "explain": self._explain,
            "mission": self._plan_mission,
            "mission_step": self._mission_step,
            "project_plan": self._plan_project,
        }
        try:
            if message.intent in handlers:
                return handlers[message.intent](message)
            return self._chat(message, on_chunk)
        except ProviderError:
            return _error("model_unavailable", UNAVAILABLE, retry_after=10)
