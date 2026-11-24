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
        # A child with a project works on that, not on the built-in example task.
        task = None if message.project_description else TASKS.get(message.current_task or "")
        prompt = harness.user_prompt(
            message,
            task=f"{task.title}: {task.instructions}" if task else None,
            extra=harness.chat_topics_note(self._topic_levels()),
        )
        history: list[Message] = [
            {"role": item["role"], "content": item["content"]}
            for item in self.session.history[-HISTORY_TURNS:]
            if item.get("role") in ("user", "assistant")
        ]
        hint = message.project_hint_level
        intent = "hint" if hint else "chat"
        system = (
            self._system("hint", message, hint_level=hint)
            if hint
            else self._system("chat", message)
        )
        text, _ = self._call_stream(
            intent,
            system,
            [*history, {"role": "user", "content": prompt}],
            on_chunk,
        )
        self.session.history = [
            *self.session.history[-HISTORY_TURNS:],
            {"role": "user", "content": harness.history_entry(message)},
            {"role": "assistant", "content": text},
        ]
        self.session.save(update_fields=["history"])
        return LearningResponse(
            mode="hint" if hint else "socratic", message=text, hint_level=hint or 0
        )

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
        level: int | None = None,
    ) -> harness.BuiltExercise:
        help_text = harness.stage_instructions(topic, stage) if stage else None
        if level:
            help_text = harness.level_instructions(level)
        explaining = intent == "explain"
        if explaining:
            help_text = harness.EXPLAIN_FORMAT_HELP
        checked = intent in ("learn", "mission_step")
        system = (
            self._system(intent, message) + "\n\n" + (help_text or harness.EXERCISE_FORMAT_HELP)
        )
        schema = harness.EXERCISE_SCHEMA
        if stage:
            schema = harness.mission_exercise_schema(stage, topic)
        elif level:
            schema = harness.learn_exercise_schema(level)
        elif explaining:
            schema = harness.EXPLAIN_SCHEMA
        prompt = harness.user_prompt(message, extra=extra)
        before = message.code_excerpt or ""

        def build(data: dict[str, Any]) -> harness.BuiltExercise:
            built = harness.build_exercise(
                data,
                max_lines=self.settings.max_code_lines_in_chat,
                prefix=prefix,
                stage=stage,
                topic=topic,
                level=level,
                kind="multiple_choice" if explaining else None,
            )
            if explaining:
                reason = harness.check_explanation(built.exercise, built.answers, built.message)
                if reason:
                    raise harness.HarnessRejected(f"Erklärung abgelehnt: {reason}")
            if checked:
                unclear = harness.check_blanks_are_clear(
                    built.exercise, built.answers, built.message
                )
                if unclear:
                    raise harness.HarnessRejected(f"Aufgabe nicht eindeutig: {unclear}")
            if allow_code:
                built.new_file_content = harness.unwrap_code_fence(built.new_file_content)
                if harness.has_stray_fence(built.new_file_content, before):
                    raise harness.HarnessRejected("Code enthält Markdown-Codeblöcke")
                reason = harness.check_generated_code(
                    before, built.new_file_content, self.settings.max_changed_lines
                )
                if reason:
                    raise harness.HarnessRejected(f"Code nach der Übung abgelehnt: {reason}")
                if message.language == "python":
                    reason = harness.check_python_syntax(before, built.new_file_content)
                    if reason:
                        raise harness.HarnessRejected(f"Code abgelehnt: {reason}")
                reason = harness.check_keeps_code(before, built.new_file_content)
                if reason:
                    raise harness.HarnessRejected(f"Code abgelehnt: {reason}")
                blanks_code = getattr(built.exercise, "code", None)
                reason = harness.check_kind_in_file(
                    built.exercise, built.answers, before, built.new_file_content
                )
                if reason:
                    raise harness.HarnessRejected(f"Code passt nicht zur Übung: {reason}")
                if checked and blanks_code:
                    reason = harness.check_blanks_in_file(
                        blanks_code, built.answers, built.new_file_content
                    )
                    if reason:
                        raise harness.HarnessRejected(f"Code passt nicht zur Übung: {reason}")
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
        built = self._exercise_round(
            "learn",
            message,
            extra=harness.learn_topics_note(self._topic_levels(), bool(message.skill_focus)),
            allow_code=True,
            prefix="learn",
            level=message.learning_level,
        )
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
