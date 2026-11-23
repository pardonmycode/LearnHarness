"""Asking the helper and deciding on its proposal for the description."""

from __future__ import annotations

from learnharness_protocol import LearningResponse
from PyQt6.QtGui import QTextCursor

from learnharness_client.domain.project_plan import MAX_DESCRIPTION, MAX_QUESTION, MAX_SKIPPED

from ....texts import T


class PanelPlanning:
    """The conversation about the project."""

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
        if text != self.plan.description:
            self.plan.suggestion = ""  # the child's own words win over an older proposal
        self.plan.description = text
        if not text.strip():
            self.plan.forget_talk()  # a new idea starts a new conversation
        self._render_helper()
        self._sync_buttons()
        self._save()

    @property
    def open_question(self) -> str | None:
        """The question the request on its way answers, if it is an answer."""
        return self.plan.question or None if self._pending_answer else None

    @property
    def skipped_questions(self) -> list[str]:
        """Questions the helper must not ask again, including one being skipped right now."""
        known = self.plan.skipped
        fresh = [self._skipping] if self._skipping and self._skipping not in known else []
        return [*known, *fresh][-MAX_SKIPPED:]

    def _request_from_description(self) -> None:
        self._request(self.plan.description.strip(), answer=None)

    def _send_reply(self) -> None:
        text = self.reply.text().strip()
        if text:
            self._request(text, answer=text)

    def _request(self, text: str, *, answer: str | None) -> None:
        if not text or not self.plan.description.strip() or self._busy or not self._online:
            return
        self._busy = True
        self._pending_answer = answer
        self._skipping = "" if answer else self.plan.question.strip()
        self._asked_description = self.plan.description
        self._sync_buttons()
        self._set_message(T.PLAN_THINKING, "neutral")
        self.plan_requested.emit(text)

    def show_response(self, response: LearningResponse) -> None:
        self._busy = False
        if self._pending_answer:
            self.plan.add_turn(self.plan.question, self._pending_answer)
            self.reply.clear()
        self.plan.add_skipped(self._skipping)
        self._skipping = ""
        self._pending_answer = None
        self._set_message("", "neutral")
        self.plan.question = response.message[:MAX_QUESTION]
        self.plan.ready = self.plan.ready or response.project_ready
        unchanged = self.plan.description == self._asked_description
        self.plan.suggestion = (response.description_suggestion or "") if unchanged else ""
        self._changed()

    def show_error(self, message: str) -> None:
        self._busy = False
        self._pending_answer = None
        self._skipping = ""
        self._set_message(message, "error")
        self._sync_buttons()

    def _accept_suggestion(self) -> None:
        text = self.plan.suggestion[:MAX_DESCRIPTION]
        if not text:
            return
        self.plan.suggestion = ""
        self.plan.description = text
        # Through the cursor, so Ctrl+Z brings the child's own text back.
        cursor = self.description.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        self.description.blockSignals(True)
        cursor.insertText(text)
        self.description.blockSignals(False)
        self._changed()

    def _reject_suggestion(self) -> None:
        self.plan.suggestion = ""
        self._changed()

    def add_finished_mission(self, title: str) -> None:
        self.plan.add_finished_mission(title)
        self._save()
