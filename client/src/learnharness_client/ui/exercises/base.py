"""Base class for exercises that never modify project files."""

from __future__ import annotations

from learnharness_protocol import ReviewResult, Submission
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..editor.gdscript_highlighter import GDScriptHighlighter
from ..theme import monospace_font, set_state


def code_view(text: str, *, accessible_name: str, max_lines: int = 8) -> QPlainTextEdit:
    """Read-only, highlighted code snippet. Nothing here can reach the project files."""
    view = QPlainTextEdit(text)
    view.setObjectName("codeView")
    view.setReadOnly(True)
    view.setFont(monospace_font())
    view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    view.setTabStopDistance(view.fontMetrics().horizontalAdvance(" ") * 4)
    view.setAccessibleName(accessible_name)
    view._highlighter = GDScriptHighlighter(view.document())  # type: ignore[attr-defined]
    lines = min(max_lines, max(1, text.count("\n") + 1))
    view.setFixedHeight(view.fontMetrics().lineSpacing() * lines + 28)
    return view


class ExerciseWidget(QFrame):
    submitted = pyqtSignal(object)

    def __init__(self, exercise, parent=None) -> None:
        super().__init__(parent)
        self.exercise = exercise
        self.setProperty("card", "true")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 14, 16, 14)
        self.layout.setSpacing(10)
        tag = QLabel(f"Übung · {exercise.skill}")
        tag.setProperty("role", "section")
        self.layout.addWidget(tag)
        self.prompt = QLabel(exercise.prompt)
        self.prompt.setWordWrap(True)
        self.prompt.setProperty("role", "subheading")
        self.layout.addWidget(self.prompt)
        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        self.result_label.hide()
        self.submit_button = QPushButton("Antwort prüfen")
        self.submit_button.setProperty("primary", "true")
        self.submit_button.setAccessibleName("Antwort prüfen")
        self.submit_button.clicked.connect(self._submit)

    def finish_layout(self) -> None:
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.submit_button)
        self.layout.addLayout(row)
        self.layout.addWidget(self.result_label)

    def answers(self) -> Submission:
        raise NotImplementedError

    def item_widgets(self) -> dict[str, QWidget]:
        """Widgets that can be marked right/wrong, keyed by the review item id."""
        return {}

    def _submit(self) -> None:
        self.submit_button.setEnabled(False)
        self.submit_button.setText("Wird geprüft …")
        self.submitted.emit(self.answers())

    def show_result(self, result: ReviewResult) -> None:
        if result.correct:
            symbol, state = "✓", "success"
        elif result.correct is False:
            symbol, state = "✗", "error"
        else:
            symbol, state = "ℹ", "info"
        text = f"{symbol}  {result.feedback}"
        if result.follow_up_question:
            text += f"\n\nWeiterdenken: {result.follow_up_question}"
        self.result_label.setText(text)
        set_state(self.result_label, callout=state)
        self.result_label.show()

        widgets = self.item_widgets()
        for item in result.per_item:
            widget = widgets.get(item.id)
            if widget is not None:
                set_state(widget, mark="correct" if item.correct else "wrong")
                if item.feedback:
                    widget.setToolTip(item.feedback)

        if result.correct:
            self.submit_button.setText("✓ Geschafft")
            self.submit_button.setEnabled(False)
        else:
            self.submit_button.setText("Nochmal prüfen")
            self.submit_button.setEnabled(True)

    def submission_failed(self) -> None:
        """The check did not reach the server; let the child try again."""
        self.submit_button.setText("Antwort prüfen")
        self.submit_button.setEnabled(True)

    def reset(self) -> None:
        self.result_label.clear()
        self.result_label.hide()
        self.submit_button.setText("Antwort prüfen")
        self.submit_button.setEnabled(True)
        for widget in self.item_widgets().values():
            set_state(widget, mark="")
