"""Explanations, project plans, hints, tasks and progress."""

from __future__ import annotations

from learnharness_protocol import (
    LearningResponse,
    ProgressUpdate,
    Skill,
    SkillLevel,
    StudentMessage,
    Task,
)

from .. import fake_content
from .base import FakeClientBase


class FakeConversation(FakeClientBase):
    """Everything around the chat."""

    def _explain(self, message: StudentMessage) -> None:
        key, explanation = fake_content.find_explanation(
            message.message, message.code_excerpt or "", message.language
        )
        response = LearningResponse(
            mode="explanation",
            message=explanation.text,
            exercise=fake_content.explanation_question(key, explanation),
        )
        self._stream_text(explanation.text, response)

    def _plan_project(self, message: StudentMessage) -> None:
        answered = len(message.project_turns) + bool(message.project_question)
        questions = fake_content.PLAN_QUESTIONS
        description = (message.project_description or "").strip()
        answering = bool(message.project_question)
        proposal = f"{description} {message.message.strip()}"[:2000] if answering else None
        fresh = [q for q in questions[answered:] if q not in message.project_skipped_questions]
        response = LearningResponse(
            mode="project_plan",
            message=fresh[0] if fresh else questions[-1],
            description_suggestion=proposal,
            project_ready=answered >= 5,
        )
        self._later(lambda: self.stream_finished.emit(response))

    def request_next_hint(self, task_id: str) -> None:
        python = task_id == "python_first_program"
        self.hint_level = min(4, self.hint_level + 1)
        hints = {
            1: "Denk an ein Koordinatensystem.",
            2: "Links und rechts liegen auf der waagerechten Achse.",
            3: "Schau dir die Eigenschaften x und y von position an.",
            4: "Probiere es zuerst in einer kleinen Lückentext-Übung.",
        }
        if python:
            hints = {
                1: "Was soll dein Programm dem Menschen zeigen?",
                2: "Für Text auf dem Bildschirm gibt es einen eigenen Befehl.",
                3: "Der Befehl heißt print.",
                4: "Text steht in Anführungszeichen innerhalb der Klammern von print.",
            }
        message = hints[self.hint_level]
        response = LearningResponse(
            mode="hint",
            message=message,
            hint_level=self.hint_level,
            hints=[message],
        )
        self._later(lambda: self.stream_finished.emit(response))
        if self.hint_level == 4 and not python:
            self._later(lambda: self.exercise_received.emit(self._fill_blank()), 2)

    def fetch_task(self, task_id: str) -> None:
        del task_id
        task = Task(
            id="move_player_right",
            title="Bewege deinen Spieler nach rechts",
            skill="Koordinaten",
            instructions=(
                "Ändere die Position deines Spielers so, dass er sich nach rechts bewegt. "
                "Schreibe den Code selbst in player.gd."
            ),
            files=["player.gd"],
        )
        self._later(lambda: self.task_received.emit(task))

    def fetch_progress(self) -> None:
        progress = ProgressUpdate(
            skills=[
                Skill(id="variables", label="Variablen", level=SkillLevel.CONFIDENT),
                Skill(id="conditions", label="Bedingungen", level=SkillLevel.WITH_HELP),
                Skill(
                    id="coordinates",
                    label="Koordinaten",
                    level=SkillLevel.ALMOST_INDEPENDENT,
                ),
                Skill(id="functions", label="Funktionen", level=SkillLevel.NOT_STARTED),
            ]
        )
        self._later(lambda: self.progress_received.emit(progress))
