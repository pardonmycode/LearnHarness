"""Level-based LearnAgent that gates generated code behind learning checks."""

from __future__ import annotations

from learnharness_protocol import LearningResponse, ReviewResult
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..exercises.base import ExerciseWidget
from ..exercises.factory import create_exercise_widget
from ..texts import T
from ..theme import set_state

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


def card(title: str) -> tuple[QFrame, QVBoxLayout]:
    """Rounded surface with a small section title."""
    frame = QFrame()
    frame.setProperty("card", "true")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(8)
    label = QLabel(title)
    label.setProperty("role", "section")
    layout.addWidget(label)
    return frame, layout


class LearnAgentPanel(QWidget):
    start_requested = pyqtSignal(str, int)
    exercise_submitted = pyqtSignal(object)

    def __init__(self, max_unlocked_level: int, parent=None) -> None:
        super().__init__(parent)
        self.max_unlocked_level = max(1, min(10, max_unlocked_level))
        self.exercise_widget: QWidget | None = None
        self._online = True
        self._busy = False

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        heading = QLabel("LearnAgent")
        heading.setProperty("role", "heading")
        intro = QLabel(
            "Beschreibe, was dein Spiel können soll. Der Agent erklärt zuerst das Thema und "
            "stellt dir eine Lernfrage. Erst wenn deine Antwort richtig ist, schreibt er den "
            "Code in dein Projekt."
        )
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")

        level_card, level_layout = card("DEIN LEVEL")
        level_row = QHBoxLayout()
        self.level_choice = QComboBox()
        self.level_choice.setAccessibleName("LearnAgent-Level")
        self.level_choice.setMinimumWidth(150)
        for level in range(1, 11):
            self.level_choice.addItem(f"Level {level}", level)
        self.unlocked_label = QLabel()
        self.unlocked_label.setProperty("role", "small")
        level_row.addWidget(self.level_choice)
        level_row.addStretch(1)
        level_row.addWidget(self.unlocked_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 10)
        self.progress.setTextVisible(False)
        self.progress.setAccessibleName("Freigeschaltete Level")
        self.level_description = QLabel()
        self.level_description.setWordWrap(True)
        level_layout.addLayout(level_row)
        level_layout.addWidget(self.progress)
        level_layout.addWidget(self.level_description)

        wish_card, wish_layout = card("WAS SOLL DEIN SPIEL KÖNNEN?")
        self.prompt = QPlainTextEdit()
        self.prompt.setPlaceholderText("Zum Beispiel: Meine Figur soll nach rechts laufen.")
        self.prompt.setFixedHeight(90)
        self.prompt.setAccessibleName("Wunsch an den LearnAgent")
        self.prompt.setTabChangesFocus(True)
        self.start_button = QPushButton("Lernrunde starten  →")
        self.start_button.setProperty("primary", "true")
        self.start_button.clicked.connect(self._start)
        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(self.start_button)
        wish_layout.addWidget(self.prompt)
        wish_layout.addLayout(button_row)

        self.feedback = QLabel()
        self.feedback.setWordWrap(True)
        self.feedback.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.feedback.hide()
        self.exercise_host = QWidget()
        self.exercise_layout = QVBoxLayout(self.exercise_host)
        self.exercise_layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(heading)
        layout.addWidget(intro)
        layout.addWidget(level_card)
        layout.addWidget(wish_card)
        layout.addWidget(self.feedback)
        layout.addWidget(self.exercise_host)
        layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self._scroll = scroll

        self.level_choice.currentIndexChanged.connect(self._level_changed)
        self.set_max_unlocked(self.max_unlocked_level)
        self.level_choice.setCurrentIndex(self.max_unlocked_level - 1)
        self._level_changed()

    def set_available(self, online: bool) -> None:
        self._online = online
        self._sync_start_button()

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._sync_start_button()

    def _sync_start_button(self) -> None:
        self.start_button.setEnabled(self._online and not self._busy)
        self.start_button.setToolTip("" if self._online else T.AGENT_OFFLINE_TIP)

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
                suffix = "" if item.isEnabled() else "  🔒"
                item.setText(f"Level {index + 1}{suffix}")
        self.progress.setValue(self.max_unlocked_level)
        self.unlocked_label.setText(f"{self.max_unlocked_level} von 10 freigeschaltet")

    def _level_changed(self) -> None:
        level = self.current_level
        if level > self.max_unlocked_level:
            self.level_choice.setCurrentIndex(self.max_unlocked_level - 1)
            return
        self.level_description.setText(LEVEL_DESCRIPTIONS[level])
        self.clear_exercise()
        self._set_feedback("", "")

    def _set_feedback(self, text: str, state: str) -> None:
        self.feedback.setText(text)
        self.feedback.setVisible(bool(text))
        set_state(self.feedback, callout=state or "neutral")

    def _start(self) -> None:
        prompt = self.prompt.toPlainText().strip()
        if not prompt:
            self._set_feedback("Beschreibe zuerst kurz deinen Spielwunsch.", "error")
            return
        self._set_busy(True)
        self.clear_exercise()
        self._set_feedback("Der LearnAgent bereitet eine passende Lernfrage vor …", "neutral")
        self.start_requested.emit(prompt, self.current_level)

    def show_response(self, response: LearningResponse) -> None:
        self._set_busy(False)
        self._set_feedback(response.message, "info")
        if response.exercise is not None:
            self.show_exercise(response.exercise)

    def show_exercise(self, exercise) -> None:
        self.clear_exercise()
        widget = create_exercise_widget(exercise, self.exercise_host)
        self.exercise_widget = widget
        self.exercise_layout.addWidget(widget)
        if isinstance(widget, ExerciseWidget):
            widget.submitted.connect(self.exercise_submitted)
        self._scroll.ensureWidgetVisible(widget)

    def show_review(self, review: ReviewResult) -> None:
        if isinstance(self.exercise_widget, ExerciseWidget):
            self.exercise_widget.show_result(review)
        if review.correct:
            self._set_feedback(
                "✓  Richtig! Jetzt darf der LearnAgent den vollständigen Code schreiben.",
                "success",
            )
        else:
            self._set_feedback(
                "Noch nicht ganz – dein Projekt wurde nicht verändert. "
                "Lies den Hinweis unten und versuche es noch einmal.",
                "error",
            )

    def show_code_result(self, written_files: list[str], explanations: list[str]) -> None:
        if written_files:
            names = ", ".join(written_files)
            explanation = "\n\n".join(explanations)
            self._set_feedback(
                f"✓  Geschafft! Der LearnAgent hat den Code in {names} geschrieben. "
                "Vorher wurde eine Sicherung angelegt – mit Strg+Z im Editor siehst du deinen "
                f"alten Code wieder.\n\nSo funktioniert der Code:\n{explanation}",
                "success",
            )
        else:
            self._set_feedback(
                "Die Antwort war richtig, aber der Code konnte nicht geschrieben werden. "
                "Dein bisheriger Inhalt wurde nicht überschrieben.",
                "error",
            )

    def show_error(self, message: str) -> None:
        self._set_busy(False)
        if isinstance(self.exercise_widget, ExerciseWidget):
            self.exercise_widget.submission_failed()
        self._set_feedback(message, "error")

    def clear_exercise(self) -> None:
        if self.exercise_widget is not None:
            self.exercise_layout.removeWidget(self.exercise_widget)
            self.exercise_widget.deleteLater()
            self.exercise_widget = None
