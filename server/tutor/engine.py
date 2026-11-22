"""What the learning server does for each request; every AI call goes through the harness."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import timedelta
from typing import Any, Literal
from uuid import uuid4

from django.core.cache import cache
from django.utils import timezone
from learnharness_protocol import (
    CodeSubmission,
    ErrorMessage,
    GeneratedFile,
    LearningResponse,
    Mission,
    MissionStep,
    ReviewItem,
    ReviewResult,
    StudentMessage,
    Submission,
    Task,
)

from children.models import Child, LearningMission

from . import harness
from .models import AiCall, AiSettings, ExerciseRecord, TutorSession
from .providers import Message, Provider, ProviderError, get_provider, parse_json

LOG = logging.getLogger(__name__)

TASKS: dict[str, Task] = {
    "move_player_right": Task(
        id="move_player_right",
        title="Bewege deinen Spieler nach rechts",
        skill="Koordinaten",
        instructions=(
            "Ändere die Position deines Spielers so, dass er sich nach rechts bewegt. "
            "Schreibe den Code selbst in player.gd."
        ),
        files=["player.gd"],
    ),
    "python_first_program": Task(
        id="python_first_program",
        title="Schreibe dein erstes Python-Programm",
        skill="Variablen",
        instructions=(
            "Lass dein Programm etwas auf dem Bildschirm anzeigen. "
            "Schreibe den Code selbst in main.py."
        ),
        files=["main.py"],
    ),
}
TASK_SKILLS = {"move_player_right": "movement", "python_first_program": "variables"}
TASK_LANGUAGES: dict[str, Literal["gdscript", "python"]] = {"python_first_program": "python"}

UNAVAILABLE = "Der Lernhelfer kann gerade nicht antworten. Versuch es gleich noch einmal."
TOO_FAST = "Langsam – du hast gerade sehr viele Fragen gestellt. Warte kurz und denk selbst nach."
HISTORY_TURNS = 8

Response = LearningResponse | ErrorMessage


def _error(code: str, message: str, retry_after: int | None = None) -> ErrorMessage:
    return ErrorMessage(code=code, message_for_child=message, retry_after=retry_after)


class Tutor:
    def __init__(
        self,
        session: TutorSession,
        settings: AiSettings | None = None,
        provider: Provider | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or AiSettings.load()
        self._provider = provider

    # Infrastructure ------------------------------------------------------------------

    @property
    def provider(self) -> Provider:
        if self._provider is None:
            self._provider = get_provider(self.settings)
        return self._provider

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
            **({"language": message.language} if message else {}),
            **extra,
        )

    # Messages over the WebSocket ---------------------------------------------------------

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
        }
        try:
            if message.intent in handlers:
                return handlers[message.intent](message)
            return self._chat(message, on_chunk)
        except ProviderError:
            return _error("model_unavailable", UNAVAILABLE, retry_after=10)

    def _chat(self, message: StudentMessage, on_chunk: Callable[[str], None] | None) -> Response:
        task = TASKS.get(message.current_task or "")
        prompt = harness.user_prompt(
            message, task=f"{task.title}: {task.instructions}" if task else None
        )
        history: list[Message] = [
            {"role": item["role"], "content": item["content"]}
            for item in self.session.history[-HISTORY_TURNS:]
            if item.get("role") in ("user", "assistant")
        ]
        text, _ = self._call_stream(
            "chat",
            self._system("chat", message),
            [*history, {"role": "user", "content": prompt}],
            on_chunk,
        )
        self.session.history = [
            *self.session.history[-HISTORY_TURNS:],
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": text},
        ]
        self.session.save(update_fields=["history"])
        return LearningResponse(mode="socratic", message=text)

    def _exercise_round(
        self,
        intent: str,
        message: StudentMessage,
        *,
        extra: str = "",
        allow_code: bool,
        prefix: str,
    ) -> harness.BuiltExercise:
        system = self._system(intent, message) + "\n\n" + harness.EXERCISE_FORMAT_HELP
        prompt = harness.user_prompt(message, extra=extra)
        before = message.code_excerpt or ""

        def build(data: dict[str, Any]) -> harness.BuiltExercise:
            built = harness.build_exercise(
                data, max_lines=self.settings.max_code_lines_in_chat, prefix=prefix
            )
            if allow_code:
                reason = harness.check_generated_code(
                    before, built.new_file_content, self.settings.max_changed_lines
                )
                if reason:
                    raise harness.HarnessRejected(f"Code nach der Übung abgelehnt: {reason}")
            else:
                built.new_file_content = ""
            return built

        built, _ = self._call_json(
            intent, system, [{"role": "user", "content": prompt}], harness.EXERCISE_SCHEMA, build
        )
        ExerciseRecord.objects.create(
            id=built.exercise.id,
            session=self.session,
            intent=intent,
            skill_id=built.skill_id,
            exercise=built.exercise.model_dump(mode="json"),
            answers=built.answers,
            explanation=built.explanation,
            generated_path=(message.file or "") if built.new_file_content else "",
            generated_content=built.new_file_content,
        )
        return built

    def _learn(self, message: StudentMessage) -> Response:
        if not message.file:
            return _error("no_file", "Öffne zuerst das Skript, in das der Code soll.")
        built = self._exercise_round("learn", message, allow_code=True, prefix="learn")
        return LearningResponse(
            mode="exercise",
            message=built.message or "Beantworte diese Frage, dann schreibe ich den Code.",
            exercise=built.exercise,
        )

    def _explain(self, message: StudentMessage) -> Response:
        if not message.code_excerpt:
            return _error("no_code", "Markiere zuerst den Code, den ich erklären soll.")
        built = self._exercise_round("explain", message, allow_code=False, prefix="explain")
        return LearningResponse(mode="explanation", message=built.message, exercise=built.exercise)

    def _plan_mission(self, message: StudentMessage) -> Response:
        def build(data: dict[str, Any]) -> tuple[Mission, str]:
            steps_data = [step for step in data.get("steps", []) if step.get("title")][:7]
            if len(steps_data) < 2:
                raise harness.HarnessRejected("Mission braucht mindestens zwei Schritte")
            if steps_data[-1].get("kind") != "try":
                title = (
                    "Starte dein Programm"
                    if message.language == "python"
                    else "Probiere es in Godot aus"
                )
                steps_data.append({"title": title, "kind": "try"})
            mission = Mission(
                id=f"wunsch-{uuid4().hex[:10]}",
                title=str(data.get("title", "Deine Mission"))[:120] or "Deine Mission",
                goal=str(data.get("goal", "")),
                skill=data.get("skill") if data.get("skill") in harness.SKILLS else None,
                steps=[
                    MissionStep(id=f"s{index}", title=str(step["title"])[:200], kind=step["kind"])
                    for index, step in enumerate(steps_data, start=1)
                ],
            )
            text, _ = harness.filter_text(
                str(data.get("message", "")), self.settings.max_code_lines_in_chat
            )
            return mission, text.strip()

        prompt = harness.user_prompt(message)
        (mission, text), _ = self._call_json(
            "mission",
            self._system("mission", message),
            [{"role": "user", "content": prompt}],
            harness.MISSION_SCHEMA,
            build,
        )
        self.session.wish_missions = {
            **self.session.wish_missions,
            mission.id: mission.model_dump(mode="json"),
        }
        self.session.save(update_fields=["wish_missions"])
        return LearningResponse(
            mode="mission", message=text or f"Deine Mission: {mission.title}", mission=mission
        )

    def _find_mission(self, mission_id: str) -> Mission | None:
        stored = LearningMission.objects.prefetch_related("steps").filter(
            mission_id=mission_id, active=True
        )
        if stored:
            return stored[0].to_protocol(with_notes=True)
        data = self.session.wish_missions.get(mission_id)
        return Mission.model_validate(data) if data else None

    def _mission_step(self, message: StudentMessage) -> Response:
        mission = self._find_mission(message.mission_id or "")
        step = (
            next((s for s in mission.steps if s.id == message.mission_step_id), None)
            if mission
            else None
        )
        if mission is None or step is None:
            return _error("unknown_step", "Diesen Missionsschritt kenne ich nicht.")
        if step.kind == "try":
            return LearningResponse(
                mode="explanation",
                message=(
                    "Speichere dein Skript und starte dein Programm."
                    if message.language == "python"
                    else "Speichere dein Skript und probiere es in Godot aus (F5)."
                ),
            )
        extra = (
            f"Mission: {mission.title} – {mission.goal}\n"
            f"Aktueller Schritt: {step.title} (Art: {step.kind})"
        )
        if step.note:
            extra += f"\nHinweis der Lehrkraft für diesen Schritt: {step.note}"
        built = self._exercise_round(
            "mission_step",
            message,
            extra=extra,
            allow_code=step.kind == "exercise",
            prefix=f"mission_{mission.id}_{step.id}",
        )
        return LearningResponse(mode="exercise", message=built.message, exercise=built.exercise)

    # HTTP requests ---------------------------------------------------------------------

    def hint(self, task_id: str) -> Response:
        task = TASKS.get(task_id)
        if task is None:
            return _error("unknown_task", "Diese Aufgabe kenne ich nicht.")
        if self._rate_limited():
            return _error("rate_limited", TOO_FAST, retry_after=30)
        level = min(4, int(self.session.hint_levels.get(task_id, 0)) + 1)
        language = TASK_LANGUAGES.get(task_id, "gdscript")
        message = StudentMessage(
            intent="chat",
            language=language,
            session_id=self.session.id,
            project_id=self.session.project_id,
            message=f"Ich brauche einen Tipp für die Aufgabe (Stufe {level}).",
        )
        prompt = harness.user_prompt(message, task=f"{task.title}: {task.instructions}")
        try:
            text, _ = self._call_stream(
                "hint",
                self._system("hint", hint_level=level, language=language),
                [{"role": "user", "content": prompt}],
                None,
            )
        except ProviderError:
            return _error("model_unavailable", UNAVAILABLE, retry_after=10)
        self.session.hint_levels = {**self.session.hint_levels, task_id: level}
        self.session.save(update_fields=["hint_levels"])
        return LearningResponse(mode="hint", message=text, hint_level=level)

    def review_submission(self, submission: Submission) -> ReviewResult | ErrorMessage:
        """Checked by the server alone: the AI never sees nor decides the answer."""
        record = ExerciseRecord.objects.filter(
            id=submission.exercise_id, session=self.session
        ).first()
        if record is None:
            return _error("unknown_exercise", "Diese Aufgabe kenne ich nicht (mehr).")
        results = harness.check_answers(record.answers, submission.answers)
        correct = all(results.values())
        per_item = [ReviewItem(id=key, correct=value) for key, value in results.items()]
        if not correct:
            return ReviewResult(
                correct=False,
                per_item=per_item,
                feedback="Noch nicht ganz. Schau dir die markierten Stellen noch einmal an.",
            )
        generated: list[GeneratedFile] = []
        if record.generated_content and record.generated_path:
            generated.append(
                GeneratedFile(
                    path=record.generated_path,
                    content=record.generated_content,
                    explanation="Die Kommentare im Code erklären jede neue Zeile.",
                )
            )
        if record.solved_at is None:
            record.solved_at = timezone.now()
            record.save(update_fields=["solved_at"])
            self._raise_skill(record.skill_id)
        return ReviewResult(
            correct=True,
            per_item=per_item,
            feedback=record.explanation or "Richtig!",
            generated_files=generated,
        )

    def review_code(self, submission: CodeSubmission) -> ReviewResult | ErrorMessage:
        task = TASKS.get(submission.task_id)
        if task is None:
            return _error("unknown_task", "Diese Aufgabe kenne ich nicht.")
        if self._rate_limited():
            return _error("rate_limited", TOO_FAST, retry_after=30)
        language = TASK_LANGUAGES.get(task.id, "gdscript")
        message = StudentMessage(
            intent="chat",
            language=language,
            session_id=self.session.id,
            project_id=self.session.project_id,
            file=submission.file,
            code_excerpt=submission.content[:16_000],
            excerpt_start_line=1,
            message="Bitte prüfe meinen Code für die Aufgabe.",
        )
        prompt = harness.user_prompt(message, task=f"{task.title}: {task.instructions}")

        def build(data: dict[str, Any]) -> ReviewResult:
            feedback, _ = harness.filter_text(
                str(data.get("feedback", "")), self.settings.max_code_lines_in_chat
            )
            lines = [int(n) for n in data.get("marked_lines", []) if isinstance(n, int) and n > 0]
            return ReviewResult(
                correct=bool(data.get("correct")),
                feedback=feedback.strip() or "Ich habe mir deinen Code angesehen.",
                marked_lines=lines[:20],
            )

        try:
            review, _ = self._call_json(
                "review",
                self._system("review", language=language),
                [{"role": "user", "content": prompt}],
                harness.REVIEW_SCHEMA,
                build,
            )
        except ProviderError:
            return _error("model_unavailable", UNAVAILABLE, retry_after=10)
        if review.correct:
            self._raise_skill(TASK_SKILLS.get(task.id, "movement"))
        return review

    def _raise_skill(self, skill_id: str) -> None:
        child: Child | None = self.session.child
        if child is None or skill_id not in harness.SKILLS:
            return
        current = child.skills.filter(skill_id=skill_id).first()
        level = min(3, (current.level if current else 0) + 1)
        child.set_skill(skill_id, harness.SKILLS[skill_id], level)


def _delivered(result: Any) -> str:
    if isinstance(result, harness.BuiltExercise):
        return result.message + "\n\n" + result.exercise.model_dump_json(indent=1)
    if isinstance(result, tuple) and result and isinstance(result[0], Mission):
        return result[1] + "\n\n" + result[0].model_dump_json(indent=1)
    if isinstance(result, ReviewResult):
        return result.feedback
    return ""
