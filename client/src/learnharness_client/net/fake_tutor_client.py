"""In-process pedagogical fake used before the learning server is available."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any

from learnharness_protocol import (
    Blank,
    Choice,
    CodeSubmission,
    FillBlanksExercise,
    FindBugExercise,
    GeneratedFile,
    HealthStatus,
    LearningResponse,
    MultipleChoiceExercise,
    OrderingExercise,
    OrderItem,
    ProgressUpdate,
    ReviewItem,
    ReviewResult,
    SessionInfo,
    Skill,
    SkillLevel,
    StudentMessage,
    Submission,
    Task,
    TextBlank,
    TextBlanksExercise,
)
from learnharness_protocol.exercises import Exercise
from PyQt6.QtCore import QObject, QTimer

from . import fake_content
from .tutor_client import ClientError, TutorClient


class FakeTutorClient(TutorClient):
    def __init__(self, parent: QObject | None = None, *, delay_ms: int = 90) -> None:
        super().__init__(parent)  # type: ignore[arg-type]  # see qtcompat
        self.delay_ms = delay_ms
        self.session_id = "fake-session-001"
        self.hint_level = 0
        self.experience_level = 0
        self._learn_level: int | None = None
        self._learn_file = "player.gd"
        self._mission_file = "player.gd"
        self._cancelled = False
        self.simulate_failure = False

    def _later(self, callback: Callable[[], None], steps: int = 1) -> None:
        QTimer.singleShot(self.delay_ms * steps, callback)

    def check_health(self) -> None:
        if self.simulate_failure:
            self._later(
                lambda: self.health_changed.emit(HealthStatus(server_ok=False, model_ok=False))
            )
            return
        self._later(
            lambda: self.health_changed.emit(
                HealthStatus(server_ok=True, model_ok=True, session_active=True, latency_ms=8)
            )
        )

    def start_session(
        self,
        project_id: str,
        student_profile_id: str,
        student_pseudonym: str,
        experience_level: int,
    ) -> None:
        del project_id, student_profile_id
        self.experience_level = experience_level
        self._later(
            lambda: self.session_started.emit(
                SessionInfo(
                    session_id=self.session_id,
                    student_pseudonym=student_pseudonym,
                    current_task_id="move_player_right",
                )
            )
        )

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

    def _stream_text(self, text: str, response: LearningResponse) -> None:
        self._cancelled = False
        self.stream_started.emit()
        words = text.split(" ")
        for index, word in enumerate(words, start=1):
            chunk = word + (" " if index < len(words) else "")
            self._later(partial(self._emit_chunk, chunk), index)
        self._later(lambda: self._finish_stream(response), len(words) + 1)

    def _explain(self, message: StudentMessage) -> None:
        key, explanation = fake_content.find_explanation(
            message.message, message.code_excerpt or ""
        )
        response = LearningResponse(
            mode="explanation",
            message=explanation.text,
            exercise=fake_content.explanation_question(key, explanation),
        )
        self._stream_text(explanation.text, response)

    def _start_mission(self, message: StudentMessage) -> None:
        content = fake_content.find_mission(message.message)
        response = LearningResponse(
            mode="mission",
            message=f"Deine Mission: {content.mission.title} {content.mission.goal}",
            mission=content.mission,
        )
        self._later(lambda: self.stream_finished.emit(response))

    def _mission_step(self, message: StudentMessage) -> None:
        self._mission_file = message.file or self._mission_file
        content = fake_content.MISSIONS.get(message.mission_id or "")
        step = content.steps.get(message.mission_step_id or "") if content else None
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

    def _start_learning_round(self, message: StudentMessage) -> None:
        self._learn_level = message.learning_level
        self._learn_file = message.file or "player.gd"
        focus = fake_content.FOCUS_ROUNDS.get(message.skill_focus or "")
        if focus is not None:
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

    def _emit_chunk(self, text: str) -> None:
        if not self._cancelled:
            self.stream_chunk.emit(text)

    def _finish_stream(self, response: LearningResponse) -> None:
        if not self._cancelled:
            self.stream_finished.emit(response)

    def cancel(self) -> None:
        self._cancelled = True
        self.error.emit(ClientError("Die Antwort wurde gestoppt.", "cancelled", False))

    def request_next_hint(self, task_id: str) -> None:
        del task_id
        self.hint_level = min(4, self.hint_level + 1)
        hints = {
            1: "Denk an ein Koordinatensystem.",
            2: "Links und rechts liegen auf der waagerechten Achse.",
            3: "Schau dir die Eigenschaften x und y von position an.",
            4: "Probiere es zuerst in einer kleinen Lückentext-Übung.",
        }
        message = hints[self.hint_level]
        response = LearningResponse(
            mode="hint",
            message=message,
            hint_level=self.hint_level,
            hints=[message],
        )
        self._later(lambda: self.stream_finished.emit(response))
        if self.hint_level == 4:
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

    def submit_exercise(self, submission: Submission) -> None:
        if submission.exercise_id.startswith("learn_level_"):
            self._submit_learning_exercise(submission)
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

    def _review(
        self, correct: bool, feedback: str, generated: list[GeneratedFile] | None = None
    ) -> None:
        result = ReviewResult(correct=correct, feedback=feedback, generated_files=generated or [])
        self._later(lambda: self.review_received.emit(result))

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

    def _submit_mission_exercise(self, submission: Submission) -> None:
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

    def _submit_learning_exercise(self, submission: Submission) -> None:
        try:
            level = int(submission.exercise_id.rsplit("_", 1)[1])
        except (ValueError, IndexError):
            level = self._learn_level or 1
        lines = submission.answers.get("lines", [])
        expected: dict[int, bool] = {
            1: submission.answers.get("choice") == "x_axis",
            2: submission.answers.get("axis") == "x",
            3: submission.answers.get("axis") == "x" and submission.answers.get("value") == "speed",
            4: submission.answers.get("axis") == "x" and submission.answers.get("value") == "speed",
            5: submission.answers.get("order") == ["extends", "speed", "process", "move"],
            6: isinstance(lines, list) and 4 in lines,
            7: submission.answers.get("axis") == "x" and submission.answers.get("value") == "speed",
            8: submission.answers.get("function") in {"_process", "_physics_process"}
            and submission.answers.get("axis") == "x",
            9: submission.answers.get("choice") == "use_delta",
            10: submission.answers.get("choice") == "explain_and_test",
        }
        correct = expected.get(level, False)
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
                "Richtig! X ist die waagerechte Achse. Jetzt darf der Agent den vollständigen "
                "Code schreiben und erklärt anschließend jeden Teil."
                if correct
                else "Das passt noch nicht. Lies die Erklärung und versuche dieselbe Frage erneut."
            ),
            generated_files=generated,
        )
        self._later(lambda: self.review_received.emit(result))

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

    @staticmethod
    def _fill_blank() -> FillBlanksExercise:
        return FillBlanksExercise(
            id="exercise_001",
            skill="Koordinaten",
            difficulty=1,
            prompt="Welche Eigenschaft bewegt den Spieler nach rechts?",
            code="position.{{blank_1}} += 10",
            blanks=[Blank(id="blank_1", options=["x", "y", "speed"])],
        )

    @staticmethod
    def choice_exercise() -> MultipleChoiceExercise:
        return MultipleChoiceExercise(
            id="exercise_002",
            skill="Koordinaten",
            difficulty=1,
            prompt="Welche Achse ist waagerecht?",
            choices=[
                Choice(id="x_axis", text="X-Achse"),
                Choice(id="y_axis", text="Y-Achse"),
            ],
        )

    @staticmethod
    def _generated_code() -> str:
        return (
            "extends Node2D\n\n"
            "# Geschwindigkeit in Pixeln pro Sekunde.\n"
            "@export var speed: float = 200.0\n\n"
            "func _process(delta: float) -> void:\n"
            "\t# X ist die waagerechte Achse. Ein positiver Wert bewegt nach rechts.\n"
            "\tposition.x += speed * delta\n"
        )

    @staticmethod
    def _exercise_for_level(level: int) -> Exercise:
        common: dict[str, Any] = {
            "id": f"learn_level_{level}",
            "skill": "Bewegung und Koordinaten",
            "difficulty": min(5, max(1, (level + 1) // 2)),
        }
        if level == 1:
            return MultipleChoiceExercise(
                **common,
                prompt="Welche Achse bewegt eine Figur nach links und rechts?",
                choices=[
                    Choice(id="x_axis", text="Die X-Achse"),
                    Choice(id="y_axis", text="Die Y-Achse"),
                ],
            )
        if level == 2:
            return FillBlanksExercise(
                **common,
                prompt="Wähle die waagerechte Achse aus.",
                code="position.{{axis}} += 10",
                blanks=[Blank(id="axis", options=["x", "y"])],
            )
        if level == 3:
            return FillBlanksExercise(
                **common,
                prompt="Ergänze Achse und Geschwindigkeit.",
                code="position.{{axis}} += {{value}} * delta",
                blanks=[
                    Blank(id="axis", options=["x", "y", "z"]),
                    Blank(id="value", options=["position", "speed", "delta"]),
                ],
            )
        if level == 4:
            return TextBlanksExercise(
                **common,
                prompt="Trage Achse und Variable ohne Auswahlhilfe ein.",
                code="position.{{axis}} += {{value}} * delta",
                blanks=[
                    TextBlank(id="axis", placeholder="Achse"),
                    TextBlank(id="value", placeholder="Variable"),
                ],
            )
        if level == 5:
            return OrderingExercise(
                **common,
                prompt="Bringe die Bausteine in die richtige Reihenfolge.",
                items=[
                    OrderItem(id="move", text="position.x += speed * delta"),
                    OrderItem(id="extends", text="extends Node2D"),
                    OrderItem(id="process", text="func _process(delta):"),
                    OrderItem(id="speed", text="var speed = 200.0"),
                ],
            )
        if level == 6:
            return FindBugExercise(
                **common,
                prompt="Welche Zeile bewegt die Figur versehentlich nach unten?",
                lines=[
                    "extends Node2D",
                    "var speed = 200.0",
                    "func _process(delta):",
                    "\tposition.y += speed * delta",
                ],
            )
        if level == 8:
            return TextBlanksExercise(
                **common,
                prompt="Ergänze Funktionsname und Achse.",
                code="func {{function}}(delta):\n\tposition.{{axis}} += speed * delta",
                blanks=[
                    TextBlank(id="function", placeholder="Funktionsname"),
                    TextBlank(id="axis", placeholder="Achse"),
                ],
            )
        if level == 9:
            return MultipleChoiceExercise(
                **common,
                prompt="Wie bleibt die Bewegung unabhängig von der Bildrate?",
                choices=[
                    Choice(id="use_delta", text="Geschwindigkeit mit delta multiplizieren"),
                    Choice(id="fixed_step", text="In jedem Bild immer 10 Pixel addieren"),
                ],
            )
        if level == 10:
            return MultipleChoiceExercise(
                **common,
                prompt="Wie prüfst du den Plan für dein eigenes Feature am besten?",
                choices=[
                    Choice(
                        id="explain_and_test",
                        text="Plan erklären, kleine Schritte testen und Fehler besprechen",
                    ),
                    Choice(id="blind", text="Code ungeprüft übernehmen"),
                ],
            )
        return TextBlanksExercise(
            **common,
            prompt="Ergänze Achse und Geschwindigkeitsvariable.",
            code="position.{{axis}} += {{value}} * delta",
            blanks=[
                TextBlank(id="axis", placeholder="Achse"),
                TextBlank(id="value", placeholder="Variable"),
            ],
        )
