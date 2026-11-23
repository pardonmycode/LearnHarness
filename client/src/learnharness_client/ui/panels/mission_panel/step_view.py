"""Shows the current step and exactly one next action for it."""

from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QWidget

from ....texts import T
from ...theme import set_state

READY = "ready"  # the step can be started
LOADING = "loading"  # waiting for the learning server
ANSWERING = "answering"  # an exercise is open
EXPLAINED = "explained"  # an explanation waits to be read
PASSED = "passed"  # solved; the child reads the feedback, then moves on
MAX_BUTTON_TITLE = 42


def _short(title: str) -> str:
    return title if len(title) <= MAX_BUTTON_TITLE else f"{title[: MAX_BUTTON_TITLE - 1]}…"


class MissionStepView:
    """Keeps step list, step card and buttons in line with the current phase."""

    def _step_number(self, step) -> int:
        return self.mission.steps.index(step) + 1

    def _render(self) -> None:
        self.choose_card.setVisible(self.mission is None)
        self.project_card.setVisible(self.mission is None and self._has_project_idea)
        self.assigned_card.setVisible(self.mission is None and bool(self.assigned))
        self.mission_card.setVisible(self.mission is not None)
        while self.steps_box.count():
            item = self.steps_box.takeAt(0)
            if item is not None and item.widget() is not None:
                item.widget().deleteLater()  # type: ignore[union-attr]
        if self.mission is None:
            self.step_title.hide()
            self._sync_buttons()
            self._sync_step_card()
            return
        if isinstance(self.mission_title, QLabel):
            self.mission_title.setText(self.mission.title)
        self.goal.setText(self.mission.goal)
        total = len(self.mission.steps)
        text = T.MISSION_PROGRESS.format(done=len(self.done), total=total)
        self.progress_label.setText(text)
        self.progress.setRange(0, total)
        self.progress.setValue(len(self.done))
        self.progress.setAccessibleName(text)
        current = self.next_step()
        for step in self.mission.steps:
            mark = "☑" if step.id in self.done else ("➜" if step is current else "☐")
            label = QLabel(f"{mark}  {step.title}")
            label.setWordWrap(True)
            if step is current:
                label.setProperty("role", "subheading")
            self.steps_box.addWidget(label)
        if current is None:
            self._set_message(T.MISSION_COMPLETE.format(title=self.mission.title), "success")
        elif self._phase == READY and current.kind == "try":
            python = self.language == "python"
            self._set_message(
                T.MISSION_TRY_TEXT_PYTHON if python else T.MISSION_TRY_TEXT, "neutral"
            )
        shown = self.active_step or (self._shown_step if self._phase == PASSED else current)
        self.step_title.setVisible(shown is not None and current is not None)
        if shown is not None:
            self.step_title.setText(
                T.MISSION_STEP_TITLE.format(
                    number=self._step_number(shown), total=total, title=shown.title
                )
            )
        self._sync_buttons()
        self._sync_step_card()

    def _main_action(self) -> str | None:
        """Text of the main button, or None when the child has something else to do first."""
        step = self.next_step()
        if self.mission is None or step is None or self._phase in (LOADING, ANSWERING):
            return None
        number = self._step_number(step)
        if self._phase == PASSED:
            return T.MISSION_NEXT_STEP.format(number=number, title=_short(step.title))
        if self._phase == EXPLAINED:
            return T.MISSION_UNDERSTOOD
        if step.kind == "try":
            return T.MISSION_TRY_WORKED
        return T.MISSION_START_STEP.format(number=number, title=_short(step.title))

    def _sync_buttons(self) -> None:
        enabled = self._online and not self._busy
        self.start_button.setEnabled(enabled)
        self.project_button.setEnabled(enabled)
        action = self._main_action()
        step = self.next_step()
        trying = self._phase == READY and step is not None and step.kind == "try"
        self.step_button.setVisible(action is not None)
        if action is not None:
            self.step_button.setText(action)
            self.step_button.setToolTip(step.title if step else "")
        # Confirming a try or moving on to one needs no server.
        needs_no_server = step is not None and (step.kind == "try" or self._phase == EXPLAINED)
        self.step_button.setEnabled(not self._busy and (enabled or needs_no_server))
        self.help_button.setVisible(trying)
        self.answer_hint.setVisible(self._phase == ANSWERING)
        self.next_project_button.setVisible(self.complete and self._has_project_idea)
        self.next_project_button.setEnabled(enabled)

    def _sync_step_card(self) -> None:
        # Before a mission exists the card only carries "planning" or error messages.
        self.step_card.setVisible(self.mission is not None or not self.message.isHidden())

    def _set_message(self, text: str, state: str) -> None:
        self.message.setText(text)
        self.message.setVisible(bool(text))
        set_state(self.message, callout=state)
        self._sync_step_card()

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._sync_buttons()

    def set_available(self, online: bool) -> None:
        self._online = online
        self._sync_buttons()

    def _reveal(self, widget: QWidget) -> None:
        """Scrolls there after Qt has laid out the new content."""
        self._reveal_target = widget
        self._reveal_timer.start()

    def _scroll_to_target(self) -> None:
        target, self._reveal_target = self._reveal_target, None
        if target is not None and not target.isHidden():
            self._scroll.ensureWidgetVisible(target)
