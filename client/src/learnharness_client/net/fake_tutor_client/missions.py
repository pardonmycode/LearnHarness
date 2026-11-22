"""Missions of the fake server."""

from __future__ import annotations

from learnharness_protocol import GeneratedFile, LearningResponse, StudentMessage, Submission

from .. import fake_content
from ..tutor_client import ClientError
from .base import FakeClientBase


class FakeMissions(FakeClientBase):
    """Mission requests and answers."""

    def _start_mission(self, message: StudentMessage) -> None:
        content = fake_content.find_mission(message.message, message.language)
        response = LearningResponse(
            mode="mission",
            message=f"Deine Mission: {content.mission.title} {content.mission.goal}",
            mission=content.mission,
        )
        self._later(lambda: self.stream_finished.emit(response))

    def _mission_step(self, message: StudentMessage) -> None:
        self._mission_file = message.file or self._mission_file
        content = fake_content.MISSIONS.get(message.mission_id or "")
        if content is not None and content.language != message.language:
            # A saved mission from another language must not write its code into this file.
            content = None
        step = content.steps.get(message.mission_step_id or "") if content else None
        if content is None and message.mission_id and message.mission_step_id:
            step = fake_content.generic_mission_step(message.mission_id, message.mission_step_id)
            if step.exercise is not None:
                self._generic_mission_steps[step.exercise.id] = step
        if step is None:
            self._later(
                lambda: self.error.emit(
                    ClientError("Diesen Missionsschritt kenne ich nicht.", "unknown_step", False)
                )
            )
            return
        response = LearningResponse(
            mode="exercise" if step.exercise else "explanation",
            message=step.message,
            exercise=step.exercise,
        )
        self._later(lambda: self.stream_finished.emit(response))

    def _submit_mission_exercise(self, submission: Submission) -> None:
        generic = self._generic_mission_steps.get(submission.exercise_id)
        if generic is not None:
            correct = all(
                submission.answers.get(key) == value for key, value in generic.answers.items()
            )
            self._review(
                correct,
                "Richtig! Schritt geschafft." if correct else "Noch nicht ganz. Überleg noch mal.",
            )
            return
        for mission_id, content in fake_content.MISSIONS.items():
            prefix = f"mission_{mission_id}_"
            if not submission.exercise_id.startswith(prefix):
                continue
            step = content.steps.get(submission.exercise_id.removeprefix(prefix))
            if step is None:
                break
            correct = all(
                submission.answers.get(key) == value for key, value in step.answers.items()
            )
            generated = (
                [
                    GeneratedFile(
                        path=self._mission_file,
                        content=step.code,
                        explanation="Die Kommentare im Code erklären jeden Schritt der Mission.",
                    )
                ]
                if correct and step.code
                else []
            )
            self._review(
                correct,
                "Richtig! Schritt geschafft."
                if correct
                else "Noch nicht ganz. Lies den Hinweis und versuche es noch einmal.",
                generated,
            )
            return
        self._review(False, "Diese Aufgabe kenne ich nicht.")
