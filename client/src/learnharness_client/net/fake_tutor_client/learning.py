"""LearnAgent rounds of the fake server."""

from __future__ import annotations

from learnharness_protocol import (
    CodeSubmission,
    GeneratedFile,
    LearningResponse,
    ReviewResult,
    StudentMessage,
    Submission,
)
from learnharness_protocol.exercises import Exercise

from .. import fake_content
from .base import FakeClientBase
from .level_content import FILL_LEVELS, is_right, level_exercise


class FakeLearning(FakeClientBase):
    """Learning rounds and code review."""

    def _start_learning_round(self, message: StudentMessage) -> None:
        self._learn_level = message.learning_level
        self._learn_file = message.file or "player.gd"
        if message.language == "python":
            self._start_python_round(message.learning_level or 1)
            return
        focus = fake_content.FOCUS_ROUNDS.get(message.skill_focus or "")
        if focus is not None and message.learning_level in FILL_LEVELS:
            exercise: Exercise = focus.exercise.model_copy(
                update={"id": f"learn_focus_{message.skill_focus}_{message.learning_level}"}
            )
            response = LearningResponse(
                mode="exercise",
                message=(
                    f"Level {message.learning_level} mit Schwerpunkt {focus.label}: Hier hast "
                    "du noch Übung gebraucht. Beantworte die Frage, dann schreibe ich den Code "
                    "mit Erklärung in dein Projekt."
                ),
                exercise=exercise,
            )
            self._later(lambda: self.stream_finished.emit(response))
            return
        exercise = self._exercise_for_level(message.learning_level or 1)
        response = LearningResponse(
            mode="exercise",
            message=(
                f"Level {message.learning_level}: Wir klären zuerst eine kleine Frage. "
                "Nur wenn sie richtig beantwortet ist, schreibe ich den vollständigen Code "
                "mit Erklärung in dein Projekt."
            ),
            exercise=exercise,
        )
        self._later(lambda: self.stream_finished.emit(response))

    def _start_python_round(self, level: int) -> None:
        exercise = level_exercise("python", level)
        response = LearningResponse(
            mode="exercise",
            message=(
                f"Level {level}: Wir klären zuerst eine kleine Frage. Nur wenn sie richtig "
                "beantwortet ist, schreibe ich den Code mit Erklärung in dein Projekt."
            ),
            exercise=exercise,
        )
        self._later(lambda: self.stream_finished.emit(response))

    def _submit_focus_exercise(self, submission: Submission) -> None:
        skill = submission.exercise_id.removeprefix("learn_focus_").rsplit("_", 1)[0]
        focus = fake_content.FOCUS_ROUNDS.get(skill)
        correct = focus is not None and all(
            submission.answers.get(blank) == answer for blank, answer in focus.answers.items()
        )
        if not correct or focus is None:
            self._review(False, "Das passt noch nicht. Schau dir die Lücken noch einmal an.")
            return
        self._review(
            True,
            f"Richtig! {focus.label} klappen schon besser. Jetzt schreibt der Agent den Code.",
            [
                GeneratedFile(
                    path=self._learn_file,
                    content=focus.code,
                    explanation=f"Die Kommentare im Code erklären dir die {focus.label}.",
                )
            ],
        )

    def _submit_learning_exercise(self, submission: Submission) -> None:
        try:
            level = int(submission.exercise_id.rsplit("_", 1)[1])
        except (ValueError, IndexError):
            level = self._learn_level or 1
        correct = is_right("godot", level, submission.answers)
        generated = []
        if correct:
            generated = [
                GeneratedFile(
                    path=self._learn_file,
                    content=self._generated_code(),
                    explanation=(
                        "Das Skript speichert die Geschwindigkeit in speed. In jedem Bild wird "
                        "die X-Position verändert. delta sorgt dafür, dass die Bewegung auf "
                        "verschiedenen Computern gleich schnell bleibt."
                    ),
                )
            ]
        result = ReviewResult(
            correct=correct,
            feedback=(
                "Richtig! Jetzt darf der Agent den vollständigen Code schreiben und erklärt "
                "anschließend jeden Teil."
                if correct
                else "Das passt noch nicht. Lies die Erklärung und versuche dieselbe Frage erneut."
            ),
            generated_files=generated,
        )
        self._later(lambda: self.review_received.emit(result))

    def _submit_python_exercise(self, submission: Submission) -> None:
        try:
            level = int(submission.exercise_id.rsplit("_", 1)[1])
        except (ValueError, IndexError):
            level = self._learn_level or 1
        correct = is_right("python", level, submission.answers)
        generated = (
            [
                GeneratedFile(
                    path=self._learn_file,
                    content=fake_content.PYTHON_GREETING_CODE,
                    explanation="Die Kommentare im Code erklären jede Zeile.",
                )
            ]
            if correct
            else []
        )
        self._review(
            correct,
            "Richtig! Jetzt schreibt der Agent den Code."
            if correct
            else "Das passt noch nicht. Schau dir die Aufgabe noch einmal an.",
            generated,
        )

    def submit_code(self, submission: CodeSubmission) -> None:
        has_position = "position" in submission.content
        has_x = ".x" in submission.content
        correct = has_position and has_x
        result = ReviewResult(
            correct=correct,
            feedback=(
                "Du verwendest die waagerechte Position. Erkläre jetzt mit deinen Worten, "
                "warum eine positive Änderung nach rechts führt."
                if correct
                else "Schau dir noch einmal an, welche Eigenschaft von position du veränderst."
            ),
            follow_up_question=(
                "Was müsste sich für eine Bewegung nach links ändern?" if correct else None
            ),
            marked_lines=[] if correct else [1],
        )
        self._later(lambda: self.review_received.emit(result))
