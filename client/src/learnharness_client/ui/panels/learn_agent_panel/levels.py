"""Level and skill-focus selection."""

from __future__ import annotations

from learnharness_protocol import Skill
from PyQt6.QtGui import QStandardItemModel

from ....domain.learning_focus import practice_candidates, suggest_focus
from ....texts import T

LEVEL_DESCRIPTIONS = T.LEVEL_DESCRIPTIONS


class AgentLevels:
    """Levels and practice focus."""

    def set_skills(self, skills: list[Skill]) -> None:
        """Offer the skills that still need practice; "automatic" picks the weakest one."""
        previous = self.focus_choice.currentData()
        suggestion = suggest_focus(skills)
        self._auto_focus = suggestion.id if suggestion else None
        self.focus_choice.clear()
        self.focus_choice.addItem(
            T.FOCUS_AUTO.format(label=suggestion.label) if suggestion else T.FOCUS_AUTO_NONE,
            None,
        )
        for skill in practice_candidates(skills):
            self.focus_choice.addItem(
                T.FOCUS_SKILL.format(label=skill.label, level=T.LEVEL_WORDS[int(skill.level)]),
                skill.id,
            )
        index = self.focus_choice.findData(previous) if previous else 0
        self.focus_choice.setCurrentIndex(max(0, index))

    @property
    def current_focus(self) -> str | None:
        chosen = self.focus_choice.currentData()
        return str(chosen) if chosen else self._auto_focus

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
                label = T.AGENT_LEVEL if item.isEnabled() else T.AGENT_LEVEL_LOCKED
                item.setText(label.format(level=index + 1))
        self.progress.setValue(self.max_unlocked_level)
        if self.level_choice.currentIndex() + 1 > self.max_unlocked_level:
            # A teacher lowered the level: jump to the highest level still unlocked.
            self.level_choice.setCurrentIndex(self.max_unlocked_level - 1)
        self.unlocked_label.setText(T.AGENT_UNLOCKED.format(level=self.max_unlocked_level))

    def _level_changed(self) -> None:
        level = self.current_level
        if level > self.max_unlocked_level:
            self.level_choice.setCurrentIndex(self.max_unlocked_level - 1)
            return
        self.level_description.setText(LEVEL_DESCRIPTIONS[level])
        self.clear_exercise()
        self._set_feedback("", "")
