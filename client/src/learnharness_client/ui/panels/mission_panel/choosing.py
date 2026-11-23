"""Choosing, restoring and resetting a mission."""

from __future__ import annotations

from learnharness_protocol import Mission, MissionList
from pydantic import ValidationError
from PyQt6.QtWidgets import QPushButton

from ....texts import T
from .step_view import READY


class MissionChoosing:
    """Which mission is active."""

    def request_mission(self, wish: str) -> None:
        wish = wish.strip()
        if not wish or self._busy or not self._online:
            return
        self._set_busy(True)
        self._set_message(T.MISSION_STARTING, "neutral")
        self.mission_requested.emit(wish)

    def set_assigned(self, listing: MissionList) -> None:
        """Missions from the teacher; finished ones stay visible with a check mark."""
        self.assigned = list(listing.missions)
        self.completed_ids |= set(listing.completed)
        while self.assigned_buttons.count():
            item = self.assigned_buttons.takeAt(0)
            if item is not None and item.widget() is not None:
                item.widget().deleteLater()  # type: ignore[union-attr]
        for mission in self.assigned:
            done = mission.id in self.completed_ids
            button = QPushButton(
                T.MISSION_ASSIGNED_DONE.format(title=mission.title) if done else mission.title
            )
            button.setToolTip(mission.goal)
            if done:
                button.setAccessibleName(T.MISSION_ASSIGNED_A11Y_DONE.format(title=mission.title))
            button.clicked.connect(lambda _=False, chosen=mission: self.start_assigned(chosen))
            self.assigned_buttons.addWidget(button)
        self._render()

    def assigned_titles(self) -> list[str]:
        texts = []
        for index in range(self.assigned_buttons.count()):
            item = self.assigned_buttons.itemAt(index)
            widget = item.widget() if item else None
            if isinstance(widget, QPushButton):
                texts.append(widget.text())
        return texts

    def start_assigned(self, mission: Mission) -> None:
        """The teacher's missions are known already: no server round trip to start them."""
        if self._busy:
            return
        self.show_mission(mission)
        self._set_message(T.MISSION_ASSIGNED_START.format(goal=mission.goal), "info")

    def show_mission(self, mission: Mission, done: set[str] | None = None) -> None:
        self._set_busy(False)
        self.mission = mission
        self.done = {step.id for step in mission.steps} & (done or set())
        self.active_step = None
        self._phase = READY
        self._shown_step = None
        self.exercises.clear()
        self.message.hide()
        self.wish.clear()
        self._render()
        self._emit_progress()

    def reset(self) -> None:
        self.mission = None
        self.done = set()
        self.active_step = None
        self._phase = READY
        self._shown_step = None
        self.exercises.clear()
        self.message.hide()
        self._render()
        self._emit_progress()

    def state(self) -> dict[str, object]:
        if self.mission is None:
            return {}
        return {"mission": self.mission.model_dump(mode="json"), "done": sorted(self.done)}

    def set_language(self, language: str) -> None:
        self.language = language
        python = language == "python"
        self.intro.setText(T.MISSION_INTRO_PYTHON if python else T.MISSION_INTRO)
        self.wish.setPlaceholderText(
            T.MISSION_WISH_PLACEHOLDER_PYTHON if python else T.MISSION_WISH_PLACEHOLDER
        )
        for owner, buttons in self._suggestions.items():
            for button in buttons:
                button.setVisible(owner == language)
        self._render()

    def restore(self, state: dict[str, object]) -> None:
        try:
            mission = Mission.model_validate(state.get("mission"))
        except ValidationError:
            return
        done = state.get("done")
        self.show_mission(
            mission, {str(item) for item in done} if isinstance(done, list) else set()
        )
