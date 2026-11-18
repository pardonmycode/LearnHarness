"""Short, skippable introduction shown once per profile."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..texts import T


class TutorialDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(T.TUTORIAL_TITLE)
        self.setMinimumSize(520, 300)
        layout = QVBoxLayout(self)
        self.pages = QStackedWidget()
        for title, text in T.TUTORIAL_STEPS:
            page = QWidget()
            page_layout = QVBoxLayout(page)
            heading = QLabel(title)
            heading.setProperty("role", "heading")
            body = QLabel(text)
            body.setWordWrap(True)
            page_layout.addWidget(heading)
            page_layout.addWidget(body)
            page_layout.addStretch(1)
            self.pages.addWidget(page)
        self.step_label = QLabel()
        self.step_label.setProperty("role", "small")

        self.skip_button = QPushButton(T.TUTORIAL_SKIP)
        self.back_button = QPushButton(T.TUTORIAL_BACK)
        self.next_button = QPushButton(T.TUTORIAL_NEXT)
        self.next_button.setProperty("primary", "true")
        self.next_button.setDefault(True)
        buttons = QHBoxLayout()
        buttons.addWidget(self.skip_button)
        buttons.addWidget(self.step_label)
        buttons.addStretch(1)
        buttons.addWidget(self.back_button)
        buttons.addWidget(self.next_button)
        layout.addWidget(self.pages, 1)
        layout.addLayout(buttons)

        self.skip_button.clicked.connect(self.reject)
        self.back_button.clicked.connect(lambda: self._go(-1))
        self.next_button.clicked.connect(lambda: self._go(1))
        self._update()

    def _go(self, step: int) -> None:
        index = self.pages.currentIndex() + step
        if index >= self.pages.count():
            self.accept()
            return
        self.pages.setCurrentIndex(max(0, index))
        self._update()

    def _update(self) -> None:
        index = self.pages.currentIndex()
        total = self.pages.count()
        self.step_label.setText(T.TUTORIAL_STEP.format(current=index + 1, total=total))
        self.back_button.setEnabled(index > 0)
        last = index == total - 1
        self.next_button.setText(T.TUTORIAL_FINISH if last else T.TUTORIAL_NEXT)
