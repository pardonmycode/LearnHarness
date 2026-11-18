"""Choose what a child should practise next, based on the skills already learned."""

from __future__ import annotations

from collections.abc import Sequence

from learnharness_protocol import Skill, SkillLevel

# Started but still needs help first, then not started yet, then almost independent.
_PRIORITY = {
    SkillLevel.WITH_HELP: 0,
    SkillLevel.NOT_STARTED: 1,
    SkillLevel.ALMOST_INDEPENDENT: 2,
}


def practice_candidates(skills: Sequence[Skill]) -> list[Skill]:
    """Skills worth practising, most useful first. Confident skills are left out."""
    open_skills = [skill for skill in skills if skill.level in _PRIORITY]
    return sorted(open_skills, key=lambda skill: _PRIORITY[SkillLevel(skill.level)])


def suggest_focus(skills: Sequence[Skill]) -> Skill | None:
    candidates = practice_candidates(skills)
    return candidates[0] if candidates else None
