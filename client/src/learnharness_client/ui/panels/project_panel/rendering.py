"""Keeps description, question, proposal and buttons in step with the plan."""

from __future__ import annotations

from ....texts import T
from ...theme import set_state


class PanelRendering:
    """Keeps the widgets in step with the plan."""

    def _changed(self) -> None:
        self._render_all()
        self._save()

    def _save(self) -> None:
        if self._has_project:
            self.plan_changed.emit(self.plan.to_dict())

    def _render_all(self) -> None:
        self._render_helper()
        self._sync_buttons()

    def _render_helper(self) -> None:
        self.question.setText(self.plan.question)
        self.helper_card.setVisible(bool(self.plan.question))
        self.ready_label.setVisible(self.plan.ready)
        self.suggestion.setText(self.plan.suggestion)
        self.suggestion_card.setVisible(bool(self.plan.suggestion))

    def _sync_buttons(self) -> None:
        has_idea = bool(self.plan.description.strip())
        can_ask = self._online and not self._busy and has_idea
        self.plan_button.setEnabled(can_ask)
        self.plan_button.setText(T.PLAN_AGAIN if self.plan.question else T.PLAN_START)
        self.build_button.setEnabled(has_idea)
        self.reply_button.setEnabled(can_ask and bool(self.reply.text().strip()))
        # The main action is answering; once the idea is clear it is starting to build.
        set_state(self.plan_button, primary="true" if not self.plan.question else "false")
        set_state(self.build_button, primary="true" if self.plan.ready else "false")

    def _set_message(self, text: str, state: str) -> None:
        self.message.setText(text)
        self.message.setVisible(bool(text))
        set_state(self.message, callout=state)
