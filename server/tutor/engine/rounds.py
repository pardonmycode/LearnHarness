"""Chat, exercise rounds, explanations and project plans."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from learnharness_protocol import LearningResponse, StudentMessage

from .. import harness
from ..models import ExerciseRecord
from ..providers import Message
from .tasks import HISTORY_TURNS, TASKS, Response, _error


class TutorRounds:
    """Conversations and exercises."""

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
        stage: int | None = None,
        topic: str | None = None,
    ) -> harness.BuiltExercise:
        help_text = harness.stage_instructions(topic, stage) if stage else None
        system = (
            self._system(intent, message) + "\n\n" + (help_text or harness.EXERCISE_FORMAT_HELP)
        )
        schema = harness.mission_exercise_schema(stage, topic) if stage else harness.EXERCISE_SCHEMA
        prompt = harness.user_prompt(message, extra=extra)
        before = message.code_excerpt or ""

        def build(data: dict[str, Any]) -> harness.BuiltExercise:
            built = harness.build_exercise(
                data,
                max_lines=self.settings.max_code_lines_in_chat,
                prefix=prefix,
                stage=stage,
                topic=topic,
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
            intent, system, [{"role": "user", "content": prompt}], schema, build
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

    def _plan_project(self, message: StudentMessage) -> Response:
        description = (message.project_description or "").strip()
        if not description:
            return _error("no_project_idea", "Beschreibe zuerst kurz dein Projekt.")
        answered = len(message.project_turns) + bool(message.project_question)
        extra = f"Bisher beantwortete Fragen: {answered}."
        if answered >= harness.PLAN_ENOUGH_ANSWERS:
            extra += " Das reicht: Sag, dass es loslegen kann, und biete eine freiwillige Frage an."

        def build(data: dict[str, Any]) -> LearningResponse:
            text, _ = harness.filter_text(
                str(data.get("message", "")), self.settings.max_code_lines_in_chat
            )
            if not text.strip():
                raise harness.HarnessRejected("Projektgespräch ohne Frage")
            clear = data.get("ready") is True and answered >= harness.PLAN_MIN_ANSWERS
            return LearningResponse(
                mode="project_plan",
                message=text.strip(),
                description_suggestion=harness.clean_description(
                    data.get("description"), description
                ),
                project_ready=clear or answered >= harness.PLAN_ENOUGH_ANSWERS,
            )

        response, _ = self._call_json(
            "project_plan",
            self._system("project_plan", message),
            [{"role": "user", "content": harness.user_prompt(message, extra=extra)}],
            harness.PROJECT_PLAN_SCHEMA,
            build,
        )
        return response
