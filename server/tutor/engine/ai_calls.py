"""Calling the AI through the harness, with logging."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import timedelta
from typing import Any

from django.core.cache import cache
from django.utils import timezone
from learnharness_protocol import LearningResponse, Mission, ReviewResult, StudentMessage

from .. import harness
from ..models import AiCall
from ..providers import Message, Provider, ProviderError, parse_json

LOG = logging.getLogger(__name__)


def _delivered(result: Any) -> str:
    if isinstance(result, harness.BuiltExercise):
        return result.message + "\n\n" + result.exercise.model_dump_json(indent=1)
    if isinstance(result, tuple) and result and isinstance(result[0], Mission):
        return result[1] + "\n\n" + result[0].model_dump_json(indent=1)
    if isinstance(result, ReviewResult):
        return result.feedback
    if isinstance(result, LearningResponse):
        return "\n".join([result.message, *result.todo_suggestions])
    return ""


class AiCalls:
    """Every AI call goes through here."""

    def _rate_limited(self) -> bool:
        since = timezone.now() - timedelta(minutes=1)
        recent = AiCall.objects.filter(
            session__profile_id=self.session.profile_id, created_at__gte=since
        ).count()
        return recent >= self.settings.requests_per_minute

    def _log(self, **fields: Any) -> AiCall:
        if not self.settings.log_prompts:
            for name in ("system_prompt", "response_text", "delivered_text"):
                fields[name] = ""
            fields["messages"] = []
        notes = fields.get("harness_notes") or []
        call = AiCall.objects.create(
            session=self.session,
            child=self.session.child,
            intervened=bool(notes),
            **fields,
        )
        self._purge_old_calls()
        return call

    def _purge_old_calls(self) -> None:
        if cache.add("tutor:purge", True, 24 * 3600):  # at most once a day
            limit = timezone.now() - timedelta(days=self.settings.log_retention_days)
            AiCall.objects.filter(created_at__lt=limit).delete()

    def _call_stream(
        self,
        intent: str,
        system: str,
        messages: list[Message],
        on_chunk: Callable[[str], None] | None,
    ) -> tuple[str, list[str]]:
        guard = harness.StreamGuard(self.settings.max_code_lines_in_chat)
        raw, delivered = [], []
        started = time.monotonic()
        provider: Provider | None = None
        try:
            provider = self.provider
            for piece in provider.stream(system, messages):
                raw.append(piece)
                shown = guard.feed(piece)
                if shown:
                    delivered.append(shown)
                    if on_chunk:
                        on_chunk(shown)
            rest = guard.finish()
            if rest:
                delivered.append(rest)
                if on_chunk:
                    on_chunk(rest)
        except ProviderError as exc:
            self._log_failure(intent, system, messages, "".join(raw), str(exc), started, provider)
            raise
        text = "".join(delivered).strip()
        self._log(
            intent=intent,
            provider=provider.provider,
            model=provider.model,
            system_prompt=system,
            messages=messages,
            response_text="".join(raw),
            delivered_text=text,
            harness_notes=guard.notes,
            input_tokens=provider.usage.input_tokens,
            output_tokens=provider.usage.output_tokens,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return text, guard.notes

    def _log_failure(
        self,
        intent: str,
        system: str,
        messages: list[Message],
        raw: str,
        error: str,
        started: float,
        provider: Provider | None,
    ) -> None:
        LOG.warning("AI call failed (%s): %s", intent, error)
        self._log(
            intent=intent,
            provider=provider.provider if provider else self.settings.provider,
            model=provider.model if provider else self.settings.active_model,
            system_prompt=system,
            messages=messages,
            response_text=raw,
            ok=False,
            error=error,
            duration_ms=int((time.monotonic() - started) * 1000),
        )

    def _call_json(
        self,
        intent: str,
        system: str,
        messages: list[Message],
        schema: dict[str, Any],
        build: Callable[[dict[str, Any]], Any],
    ) -> tuple[Any, list[str]]:
        """Ask for structured output and build it; one retry with the reason if it breaks a
        rule. Each attempt is logged."""
        attempt_messages = list(messages)
        notes: list[str] = []
        for attempt in range(2):
            started = time.monotonic()
            provider: Provider | None = None
            text = ""
            try:
                provider = self.provider
                text = provider.complete_json(system, attempt_messages, schema)
                result = build(parse_json(text))
            except (ProviderError, harness.HarnessRejected, ValueError) as exc:
                reason = str(exc)
                notes.append(f"Versuch {attempt + 1} verworfen: {reason}")
                self._log(
                    intent=intent,
                    provider=provider.provider if provider else self.settings.provider,
                    model=provider.model if provider else self.settings.active_model,
                    system_prompt=system,
                    messages=attempt_messages,
                    response_text=text,
                    harness_notes=[f"verworfen: {reason}"],
                    ok=False,
                    error=reason,
                    input_tokens=provider.usage.input_tokens if provider else None,
                    output_tokens=provider.usage.output_tokens if provider else None,
                    duration_ms=int((time.monotonic() - started) * 1000),
                )
                if isinstance(exc, ProviderError) and not text:
                    raise  # unreachable or refused: retrying does not help
                attempt_messages = [
                    *messages,
                    {"role": "assistant", "content": text or "(keine gültige Antwort)"},
                    {
                        "role": "user",
                        "content": f"Deine Antwort war nicht gültig: {reason}. "
                        "Antworte noch einmal genau im verlangten Format.",
                    },
                ]
                continue
            extra = getattr(result, "notes", [])
            self._log(
                intent=intent,
                provider=provider.provider,
                model=provider.model,
                system_prompt=system,
                messages=attempt_messages,
                response_text=text,
                delivered_text=_delivered(result),
                harness_notes=notes + extra,
                input_tokens=provider.usage.input_tokens,
                output_tokens=provider.usage.output_tokens,
                duration_ms=int((time.monotonic() - started) * 1000),
            )
            return result, notes + extra
        raise ProviderError("; ".join(notes))

    def _system(self, intent: str, message: StudentMessage | None = None, **extra: Any) -> str:
        return harness.system_prompt(
            intent,
            self.settings,
            learning_level=message.learning_level if message else None,
            experience_level=message.experience_level if message else self.session.experience_level,
            **(
                {
                    "language": message.language,
                    "active_todo": bool(message.active_todo),
                    "game": harness.is_game_project(message.language, message.project_description),
                }
                if message
                else {}
            ),
            **extra,
        )
