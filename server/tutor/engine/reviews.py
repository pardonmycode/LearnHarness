"""Hints and checking of submissions."""

from __future__ import annotations

from typing import Any

from django.db.models import F
from django.utils import timezone
from learnharness_protocol import (
    CodeSubmission,
    ErrorMessage,
    GeneratedFile,
    LearningResponse,
    ReviewItem,
    ReviewResult,
    StudentMessage,
    Submission,
)

from children.models import Child

from .. import harness
from ..models import ExerciseRecord
from ..providers import ProviderError
from .tasks import TASK_LANGUAGES, TASK_SKILLS, TASKS, TOO_FAST, UNAVAILABLE, Response, _error


class TutorReviews:
    """Hints and reviews."""

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
            if record.solved_at is None:
                ExerciseRecord.objects.filter(pk=record.pk).update(
                    wrong_attempts=F("wrong_attempts") + 1
                )
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
                    content=harness.apply_typed_answers(
                        record.generated_content,
                        str(record.exercise.get("code") or ""),
                        record.answers,
                        submission.answers,
                    ),
                    explanation="Die Kommentare im Code erklären jede neue Zeile.",
                )
            )
        if record.solved_at is None:
            record.solved_at = timezone.now()
            record.save(update_fields=["solved_at"])
            if record.intent == "mission_step":
                self._advance_topic(record.skill_id)
            else:
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
        before = current.level if current else 0
        # Mission topics move up through their stages only, see _advance_topic.
        ceiling = 1 if skill_id in harness.MISSION_TOPICS else 3
        level = max(before, min(ceiling, before + 1))
        child.set_skill(skill_id, harness.SKILLS[skill_id], level)
