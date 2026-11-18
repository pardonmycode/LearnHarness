"""Interactive code explainer: questions about the selected code plus a check question."""

from __future__ import annotations

from learnharness_protocol import LearningResponse, ReviewResult
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...domain.code_questions import code_questions
from ...texts import T
from ..exercises.base import code_view
from ..theme import set_state
from .exercise_host import ExerciseHost
from .learn_agent_panel import card


class ExplainPanel(QWidget):
    take_selection_requested = pyqtSignal()
    question_asked = pyqtSignal(str)  # question about self.code
    exercise_submitted = pyqtSignal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.code = ""
        self.file = ""
        self.start_line = 1
        self._online = True
        self._busy = False
        self._streamed = ""

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        heading = QLabel(T.EXPLAIN_HEADING)
        heading.setProperty("role", "heading")
        intro = QLabel(T.EXPLAIN_INTRO)
        intro.setWordWrap(True)
        intro.setProperty("role", "muted")
        self.take_button = QPushButton(T.EXPLAIN_TAKE_SELECTION)
        self.take_button.clicked.connect(self.take_selection_requested)

        self.code_card, code_layout = card(T.EXPLAIN_HEADING)
        self.code_title = code_layout.itemAt(0).widget()  # type: ignore[union-attr]
        self.code_view = code_view("", accessible_name=T.EXPLAIN_CODE_A11Y, max_lines=10)
        code_layout.addWidget(self.code_view)
        self.code_card.hide()

        self.questions_card, questions_layout = card(T.EXPLAIN_QUESTIONS)
        self.question_buttons = QVBoxLayout()
        questions_layout.addLayout(self.question_buttons)
        own_row = QHBoxLayout()
        self.own_question = QLineEdit()
        self.own_question.setPlaceholderText(T.EXPLAIN_OWN_QUESTION)
        self.own_question.setAccessibleName(T.EXPLAIN_OWN_A11Y)
        self.own_question.returnPressed.connect(self._ask_own)
        self.ask_button = QPushButton(T.EXPLAIN_ASK)
        self.ask_button.setProperty("primary", "true")
        self.ask_button.clicked.connect(self._ask_own)
        own_row.addWidget(self.own_question, 1)
        own_row.addWidget(self.ask_button)
        questions_layout.addLayout(own_row)
        self.questions_card.hide()

        self.answer_card, answer_layout = card(T.EXPLAIN_ANSWER)
        self.answer = QLabel()
        self.answer.setWordWrap(True)
        self.answer.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.check_label = QLabel(T.EXPLAIN_CHECK)
        self.check_label.setProperty("role", "subheading")
        self.check_label.hide()
        self.exercises = ExerciseHost(self)
        self.exercises.submitted.connect(self.exercise_submitted)
        self.feedback = QLabel()
        self.feedback.setWordWrap(True)
        self.feedback.setProperty("callout", "neutral")
        self.feedback.hide()
        answer_layout.addWidget(self.answer)
        answer_layout.addWidget(self.check_label)
        answer_layout.addWidget(self.exercises.widget)
        answer_layout.addWidget(self.feedback)
        self.answer_card.hide()

        layout.addWidget(heading)
        layout.addWidget(intro)
        layout.addWidget(self.take_button)
        layout.addWidget(self.code_card)
        layout.addWidget(self.questions_card)
        layout.addWidget(self.answer_card)
        layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self._scroll = scroll

    # Code and questions ----------------------------------------------------------

    def set_code(self, file: str, code: str, start_line: int) -> None:
        self.file, self.code, self.start_line = file, code, start_line
        end_line = start_line + max(0, code.count("\n"))
        if isinstance(self.code_title, QLabel):
            self.code_title.setText(
                T.EXPLAIN_FILE.format(file=file, start=start_line, end=end_line)
            )
        self.code_view.setPlainText(code)
        lines = min(10, max(1, code.count("\n") + 1))
        # + frame padding and room for the horizontal scroll bar
        self.code_view.setFixedHeight(self.code_view.fontMetrics().lineSpacing() * lines + 46)
        self.code_card.show()
        while self.question_buttons.count():
            item = self.question_buttons.takeAt(0)
            if item is not None and item.widget() is not None:
                item.widget().deleteLater()  # type: ignore[union-attr]
        for question in code_questions(code):
            button = QPushButton(question)
            button.setProperty("role", "chip")
            button.clicked.connect(lambda _=False, text=question: self.ask(text))
            self.question_buttons.addWidget(button)
        self.questions_card.show()
        self.answer_card.hide()
        self._sync_buttons()

    def show_no_code(self) -> None:
        self.answer_card.show()
        self.answer.setText(T.EXPLAIN_NO_CODE)

    def question_texts(self) -> list[str]:
        texts = []
        for index in range(self.question_buttons.count()):
            item = self.question_buttons.itemAt(index)
            widget = item.widget() if item else None
            if isinstance(widget, QPushButton):
                texts.append(widget.text())
        return texts

    def ask(self, question: str) -> None:
        question = question.strip()
        if not question or not self.code or self._busy or not self._online:
            return
        self._busy = True
        self._sync_buttons()
        self.exercises.clear()
        self.check_label.hide()
        self.feedback.hide()
        self.answer_card.show()
        self.answer.setText(T.EXPLAIN_THINKING)
        self._streamed = ""
        self.question_asked.emit(question)

    def _ask_own(self) -> None:
        text = self.own_question.text()
        if text.strip():
            self.own_question.clear()
            self.ask(text)

    # Answers -------------------------------------------------------------------------

    def begin_stream(self) -> None:
        self._streamed = ""

    def append_stream_chunk(self, text: str) -> None:
        self._streamed += text
        self.answer.setText(self._streamed)

    def show_response(self, response: LearningResponse) -> None:
        self._busy = False
        self._sync_buttons()
        self.answer.setText(response.message)
        if response.exercise is not None:
            self.check_label.show()
            widget = self.exercises.show(response.exercise)
            self._scroll.ensureWidgetVisible(widget)

    def show_review(self, review: ReviewResult) -> None:
        self.exercises.show_result(review)
        self.feedback.setText(T.EXPLAIN_CORRECT if review.correct else T.EXPLAIN_NOT_YET)
        self.feedback.show()
        set_state(self.feedback, callout="success" if review.correct else "error")

    def show_error(self, message: str) -> None:
        self._busy = False
        self._sync_buttons()
        self.exercises.submission_failed()
        self.answer_card.show()
        self.answer.setText(message)

    def set_available(self, online: bool) -> None:
        self._online = online
        self._sync_buttons()

    def _sync_buttons(self) -> None:
        enabled = self._online and not self._busy
        self.ask_button.setEnabled(enabled)
        for index in range(self.question_buttons.count()):
            item = self.question_buttons.itemAt(index)
            if item is not None and item.widget() is not None:
                item.widget().setEnabled(enabled)  # type: ignore[union-attr]
