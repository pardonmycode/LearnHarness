"""Base class for exercises that never modify project files."""

from __future__ import annotations

import re

from learnharness_protocol import ReviewResult, Submission
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from learnharness_client import design

from ...texts import T
from ..editor.gdscript_highlighter import GDScriptHighlighter
from ..theme import colors, monospace_font, set_state


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
    view.setFixedHeight(
        view.fontMetrics().lineSpacing() * lines + design.EXERCISE_CODE_EXTRA_HEIGHT
    )
    return view


_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_\-]+)\s*\}\}")


def blank_order(code: str) -> list[str]:
    """Blank ids in the order they appear in the code (each id once)."""
    seen: list[str] = []
    for match in _PLACEHOLDER.finditer(code):
        if match.group(1) not in seen:
            seen.append(match.group(1))
    return seen


def _code_label(text: str) -> QLabel:
    # Non-breaking spaces keep indentation and alignment exactly as written.
    label = QLabel(text.replace("\t", "    ").replace(" ", " "))
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setFont(monospace_font())
    label.setStyleSheet("background: transparent; border: none; padding: 0;")
    return label


def inline_blanks_view(
    code: str,
    inputs: dict[str, QWidget],
    *,
    accessible_name: str,
) -> QFrame:
    """Read-only code card with the answer widgets embedded where the gaps are.

    Placeholders whose id has no input stay visible as text; inputs that do not
    appear in the code are added in an extra row so nothing becomes unreachable.
    """
    c = colors()
    frame = QFrame()
    frame.setObjectName("inlineCode")
    frame.setAccessibleName(accessible_name)
    frame.setStyleSheet(
        f"QFrame#inlineCode {{ background: {c.editor_bg}; border: 1px solid {c.border};"
        " border-radius: 8px; }"
        f" QFrame#inlineCode QLabel {{ color: {c.text}; }}"
    )
    rows = QVBoxLayout(frame)
    rows.setContentsMargins(*design.FEEDBACK_MARGINS)
    rows.setSpacing(design.FEEDBACK_SPACING)
    used: set[str] = set()
    for line in code.splitlines() or [""]:
        row = QHBoxLayout()
        row.setSpacing(design.FEEDBACK_ROW_SPACING)
        position = 0
        for match in _PLACEHOLDER.finditer(line):
            blank_id = match.group(1)
            widget = inputs.get(blank_id)
            if widget is None or blank_id in used:
                continue
            if match.start() > position:
                row.addWidget(_code_label(line[position : match.start()]))
            row.addWidget(widget)
            used.add(blank_id)
            position = match.end()
        rest = line[position:]
        if rest or row.count() == 0:
            row.addWidget(_code_label(rest or " "))
        row.addStretch(1)
        rows.addLayout(row)
    missing = [blank_id for blank_id in inputs if blank_id not in used]
    if missing:
        row = QHBoxLayout()
        row.addWidget(_code_label(T.EXERCISE_MORE_BLANKS))
        for blank_id in missing:
            row.addWidget(inputs[blank_id])
        row.addStretch(1)
        rows.addLayout(row)
    return frame


def chain_tab_order(widgets: list[QWidget], after: QWidget | None = None) -> None:
    """Tab walks through the gaps in reading order, then on to the submit button."""
    chain = [*widgets, after] if after is not None else list(widgets)
    for first, second in zip(chain, chain[1:], strict=False):
        QWidget.setTabOrder(first, second)


class ExerciseWidget(QFrame):
    submitted = pyqtSignal(object)

    def __init__(self, exercise, parent=None) -> None:
        super().__init__(parent)
        self.exercise = exercise
        self.setProperty("card", "true")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(*design.CARD_MARGINS)
        self.layout.setSpacing(design.EXERCISE_SPACING)
        tag = QLabel(T.EXERCISE_TAG.format(skill=exercise.skill))
        tag.setProperty("role", "section")
        self.layout.addWidget(tag)
        self.prompt = QLabel(exercise.prompt)
        self.prompt.setWordWrap(True)
        self.prompt.setProperty("role", "subheading")
        self.layout.addWidget(self.prompt)
        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        self.result_label.hide()
        self.submit_button = QPushButton(T.EXERCISE_SUBMIT)
        self.submit_button.setProperty("primary", "true")
        self.submit_button.setAccessibleName(T.EXERCISE_SUBMIT)
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
        self.submit_button.setText(T.EXERCISE_CHECKING)
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
            text += T.EXERCISE_FOLLOW_UP.format(question=result.follow_up_question)
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
            self.submit_button.setText(T.EXERCISE_DONE)
            self.submit_button.setEnabled(False)
        else:
            self.submit_button.setText(T.EXERCISE_RETRY)
            self.submit_button.setEnabled(True)

    def submission_failed(self) -> None:
        """The check did not reach the server; let the child try again."""
        self.submit_button.setText(T.EXERCISE_SUBMIT)
        self.submit_button.setEnabled(True)

    def reset(self) -> None:
        self.result_label.clear()
        self.result_label.hide()
        self.submit_button.setText(T.EXERCISE_SUBMIT)
        self.submit_button.setEnabled(True)
        for widget in self.item_widgets().values():
            set_state(widget, mark="")
