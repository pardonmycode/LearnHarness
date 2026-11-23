"""In-process pedagogical fake used before the learning server is available."""

from __future__ import annotations

from functools import partial

from learnharness_protocol import (
    GeneratedFile,
    LearningResponse,
    ReviewItem,
    ReviewResult,
    StudentMessage,
    Submission,
)

from .. import fake_content
from ..tutor_client import ClientError
from .base import FakeClientBase
from .conversation import FakeConversation
from .learning import FakeLearning
from .level_exercises import FakeExercises
from .missions import FakeMissions

__all__ = ["FakeTutorClient"]


class FakeTutorClient(FakeMissions, FakeLearning, FakeConversation, FakeClientBase, FakeExercises):
    def send_message(self, message: StudentMessage) -> None:
        if self.simulate_failure:
            self._later(
                lambda: self.error.emit(
                    ClientError("Ich kann den Lernhelfer gerade nicht erreichen.", "fake_timeout")
                )
            )
            return
        if message.intent == "explain":
            self._explain(message)
            return
        if message.intent == "project_plan":
            self._plan_project(message)
            return
        if message.intent == "mission":
            self._start_mission(message)
            return
        if message.intent == "mission_step":
            self._mission_step(message)
            return
        if message.learning_level is not None:
            self._start_learning_round(message)
            return
        self._cancelled = False
        self.stream_started.emit()
        questions = {
            0: "Wenn etwas nach rechts geht: Welche Koordinate ändert sich – X oder Y?",
            1: "Welche Koordinate verändert die Bewegung nach rechts – X oder Y?",
            2: "Welche Komponente von position musst du für eine Bewegung nach rechts verändern?",
            3: "Welche Vector2-Komponente und welches Vorzeichen brauchst du für die Bewegung?",
        }
        text = questions.get(self.experience_level, questions[0])
        if message.language == "python":
            text = "Was soll dein Programm als Erstes auf dem Bildschirm anzeigen?"
        if message.active_todo:
            text = f"Zu deinem To-do „{message.active_todo}“: Was ist der kleinste erste Schritt?"
        words = [
            word + (" " if index < len(text.split()) - 1 else "")
            for index, word in enumerate(text.split())
        ]
        for index, word in enumerate(words, start=1):
            self._later(partial(self._emit_chunk, word), index)
        self._later(
            lambda: self._finish_stream(
                LearningResponse(
                    mode="socratic",
                    message=text,
                    hint_level=self.hint_level,
                )
            ),
            len(words) + 1,
        )

    def submit_exercise(self, submission: Submission) -> None:
        if submission.exercise_id.startswith("learn_level_"):
            self._submit_learning_exercise(submission)
            return
        if submission.exercise_id.startswith("learn_python_"):
            correct = submission.answers.get("choice") == "right"
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
                "Richtig! print zeigt Text an. Jetzt schreibt der Agent den Code."
                if correct
                else "Das passt noch nicht. Welcher Befehl gibt etwas aus?",
                generated,
            )
            return
        if submission.exercise_id.startswith("learn_focus_"):
            self._submit_focus_exercise(submission)
            return
        if submission.exercise_id.startswith("explain_"):
            correct = submission.answers.get("choice") == "right"
            self._review(
                correct,
                "Genau! Du hast die Erklärung verstanden."
                if correct
                else "Noch nicht ganz. Lies die Erklärung noch einmal in Ruhe.",
            )
            return
        if submission.exercise_id.startswith("mission_"):
            self._submit_mission_exercise(submission)
            return
        answer = submission.answers.get("blank_1")
        if answer is None:
            selected = submission.answers.get("choice")
            correct = selected == "x_axis" or selected == ["x_axis"]
            item_id = "choice"
        else:
            correct = answer == "x"
            item_id = "blank_1"
        result = ReviewResult(
            correct=correct,
            per_item=[ReviewItem(id=item_id, correct=correct)],
            feedback=(
                "Gut erkannt: X steht für links und rechts."
                if correct
                else "Noch nicht ganz. Welche Achse verläuft waagerecht?"
            ),
            follow_up_question="Wie würdest du die Bewegung nach links beschreiben?"
            if correct
            else None,
        )
        self._later(lambda: self.review_received.emit(result))
