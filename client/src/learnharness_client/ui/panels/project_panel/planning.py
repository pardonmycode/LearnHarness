"""Asking the helper and deciding on its suggestions."""

from __future__ import annotations

from learnharness_protocol import LearningResponse

from learnharness_client.domain.project_plan import MAX_DESCRIPTION, MAX_QUESTION, MAX_TODOS

from ....texts import T


class PanelPlanning:
    """Planning with the helper."""

    def _description_changed(self) -> None:
        text = self.description.toPlainText()
        if len(text) > MAX_DESCRIPTION:
            cursor = self.description.textCursor()
            position = min(cursor.position(), MAX_DESCRIPTION)
            text = text[:MAX_DESCRIPTION]
            self.description.blockSignals(True)
            self.description.setPlainText(text)
            cursor = self.description.textCursor()
            cursor.setPosition(position)
            self.description.setTextCursor(cursor)
            self.description.blockSignals(False)
        self.plan.description = text
        self._sync_buttons()
        self._save()

    def _request_from_description(self) -> None:
        self._request(self.plan.description.strip())

    def _send_reply(self) -> None:
        text = self.reply.text().strip()
        if text:
            self._request(text)

    def _request(self, text: str) -> None:
        if not text or not self.plan.description.strip() or self._busy or not self._online:
            return
        self._busy = True
        self._sync_buttons()
        self._set_message(T.PLAN_THINKING, "neutral")
        self.plan_requested.emit(text)

    def show_response(self, response: LearningResponse) -> None:
        self._busy = False
        self.reply.clear()
        self._set_message("", "neutral")
        self.plan.question = response.message[:MAX_QUESTION]
        self.plan.set_suggestions(response.todo_suggestions)
        self._render_helper()
        self._sync_buttons()
        self._save()

    def show_error(self, message: str) -> None:
        self._busy = False
        self._set_message(message, "error")
        self._sync_buttons()

    def _accept(self, text: str) -> None:
        if not self.plan.accept_suggestion(text):
            self._set_message(T.PLAN_LIST_FULL.format(count=MAX_TODOS), "error")
            return
        self._changed()

    def _reject(self, text: str) -> None:
        if text in self.plan.suggestions:
            self.plan.suggestions.remove(text)
            self._changed()

    def _accept_all(self) -> None:
        for text in list(self.plan.suggestions):
            if not self.plan.accept_suggestion(text):
                self._set_message(T.PLAN_LIST_FULL.format(count=MAX_TODOS), "error")
                break
        self._changed()
