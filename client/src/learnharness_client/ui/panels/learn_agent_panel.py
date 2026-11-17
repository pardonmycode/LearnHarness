"""Level-based LearnAgent that gates generated code behind learning checks."""

from __future__ import annotations

from learnharness_protocol import LearningResponse, ReviewResult
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtWidgets import (
    QComboBox,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..exercises.base import ExerciseWidget
from ..exercises.factory import create_exercise_widget

LEVEL_DESCRIPTIONS = {
    1: "Einfache Verständnisfragen. Erst nach einer richtigen Antwort schreibt der Agent den Code.",
    2: "Einfache Code-Lücken mit einem Dropdown-Menü.",
    3: "Schwierigere Code-Lücken mit mehreren Dropdown-Menüs.",
    4: "Code-Lücken ohne Auswahl: Du trägst kurze Begriffe selbst ein.",
    5: "Bringe fertige Code-Bausteine in die richtige Reihenfolge.",
    6: "Finde einen Fehler in einem kurzen Code-Beispiel.",
    7: "Ergänze wichtige Ausdrücke mit kleinen Hinweisen.",
    8: "Plane eine Funktion und ergänze mehrere zusammenhängende Teile.",
    9: "Entscheide selbst über den Lösungsweg und begründe ihn.",
    10: "Beschreibe ein eigenes Spielfeature und prüfe den Plan des Agenten.",
}


class LearnAgentPanel(QWidget):
    start_requested = pyqtSignal(str, int)
    exercise_submitted = pyqtSignal(object)

    def __init__(self, max_unlocked_level: int, parent=None) -> None:
        super().__init__(parent)
        self.max_unlocked_level = max(1, min(10, max_unlocked_level))
        self.exercise_widget: QWidget | None = None
        layout = QVBoxLayout(self)
        heading = QLabel("LearnAgent")
        heading.setStyleSheet("font-size: 19px; font-weight: bold;")
        intro = QLabel(
            "Beschreibe, was dein Spiel können soll. Der Agent erklärt zuerst das Thema und "
            "stellt eine Lernfrage. Vollständiger Code wird nur nach einer richtigen Antwort "
            "sicher in dein Projekt geschrieben."
        )
        intro.setWordWrap(True)
        self.level_choice = QComboBox()
        self.level_choice.setAccessibleName("LearnAgent-Level")
        for level in range(1, 11):
            self.level_choice.addItem(f"Level {level}", level)
        self.level_description = QLabel()
        self.level_description.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setRange(1, 10)
        self.progress.setValue(self.max_unlocked_level)
        self.progress.setFormat("Freigeschaltet bis Level %v")
        self.prompt = QPlainTextEdit()
        self.prompt.setPlaceholderText(
            "Was soll dein Spiel können? Zum Beispiel: Meine Figur soll nach rechts laufen."
        )
        self.prompt.setMaximumHeight(100)
        self.prompt.setAccessibleName("Wunsch an den LearnAgent")
        self.start_button = QPushButton("Lernrunde starten")
        self.start_button.clicked.connect(self._start)
        self.level_choice.currentIndexChanged.connect(self._level_changed)
        self.feedback = QLabel()
        self.feedback.setWordWrap(True)
        self.feedback.setStyleSheet("padding: 6px;")
        self.exercise_host = QWidget()
        self.exercise_layout = QVBoxLayout(self.exercise_host)
        self.exercise_layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(heading)
        layout.addWidget(intro)
        layout.addWidget(self.level_choice)
        layout.addWidget(self.level_description)
        layout.addWidget(self.progress)
        layout.addWidget(self.prompt)
        layout.addWidget(self.start_button)
        layout.addWidget(self.feedback)
        layout.addWidget(self.exercise_host, 1)
        self.set_max_unlocked(self.max_unlocked_level)
        self.level_choice.setCurrentIndex(self.max_unlocked_level - 1)
        self._level_changed()

    @property
    def current_level(self) -> int:
        return int(self.level_choice.currentData())

    def set_max_unlocked(self, level: int) -> None:
        self.max_unlocked_level = max(1, min(10, level))
        model = self.level_choice.model()
        if isinstance(model, QStandardItemModel):
            for index in range(self.level_choice.count()):
                item = model.item(index)
                item.setEnabled(index + 1 <= self.max_unlocked_level)
                suffix = "" if item.isEnabled() else " 🔒"
                item.setText(f"Level {index + 1}{suffix}")
        self.progress.setValue(self.max_unlocked_level)

    def _level_changed(self) -> None:
        level = self.current_level
        if level > self.max_unlocked_level:
            self.level_choice.setCurrentIndex(self.max_unlocked_level - 1)
            return
        self.level_description.setText(LEVEL_DESCRIPTIONS[level])
        self.clear_exercise()
        self.feedback.clear()

    def _start(self) -> None:
        prompt = self.prompt.toPlainText().strip()
        if not prompt:
            self.feedback.setText("Beschreibe zuerst kurz deinen Spielwunsch.")
            self.feedback.setStyleSheet("color: #b91c1c; padding: 6px;")
            return
        self.start_button.setEnabled(False)
        self.feedback.setText("Der LearnAgent bereitet eine passende Lernfrage vor …")
        self.feedback.setStyleSheet("color: #1d4ed8; padding: 6px;")
        self.start_requested.emit(prompt, self.current_level)

    def show_response(self, response: LearningResponse) -> None:
        self.start_button.setEnabled(True)
        self.feedback.setText(response.message)
        self.feedback.setStyleSheet("color: #0f172a; padding: 6px;")
        if response.exercise is not None:
            self.show_exercise(response.exercise)

    def show_exercise(self, exercise) -> None:
        self.clear_exercise()
        widget = create_exercise_widget(exercise, self.exercise_host)
        self.exercise_widget = widget
        self.exercise_layout.addWidget(widget)
        if isinstance(widget, ExerciseWidget):
            widget.submitted.connect(self.exercise_submitted)

    def show_review(self, review: ReviewResult) -> None:
        if isinstance(self.exercise_widget, ExerciseWidget):
            self.exercise_widget.show_result(review)
        if review.correct:
            self.feedback.setText(
                f"✓ {review.feedback}\n\nDie Antwort ist richtig. Der vollständige Code darf jetzt "
                "geschrieben werden."
            )
            self.feedback.setStyleSheet("color: #15803d; padding: 6px; font-weight: bold;")
        else:
            self.feedback.setText(
                f"✗ {review.feedback}\n\nDer Code wurde nicht geschrieben. "
                "Versuche die Frage noch einmal."
            )
            self.feedback.setStyleSheet("color: #b91c1c; padding: 6px; font-weight: bold;")

    def show_code_result(self, written_files: list[str], explanations: list[str]) -> None:
        if written_files:
            names = ", ".join(written_files)
            explanation = "\n\n".join(explanations)
            self.feedback.setText(
                f"✓ Richtig gelöst. Der LearnAgent hat den vollständigen Code in {names} "
                f"geschrieben und vorher eine Sicherung angelegt.\n\nErklärung:\n{explanation}"
            )
        else:
            self.feedback.setText(
                "Die Antwort war richtig, aber der Code konnte nicht geschrieben werden. "
                "Dein bisheriger Inhalt wurde nicht überschrieben."
            )

    def show_error(self, message: str) -> None:
        self.start_button.setEnabled(True)
        self.feedback.setText(message)
        self.feedback.setStyleSheet("color: #b91c1c; padding: 6px;")

    def clear_exercise(self) -> None:
        if self.exercise_widget is not None:
            self.exercise_layout.removeWidget(self.exercise_widget)
            self.exercise_widget.deleteLater()
            self.exercise_widget = None
