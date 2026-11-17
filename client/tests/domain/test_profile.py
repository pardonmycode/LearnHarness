from __future__ import annotations

import pytest

from learnharness_client.domain.profile import ExperienceLevel, StudentProfile


def test_profile_normalizes_pseudonym_and_roundtrips() -> None:
    profile = StudentProfile.create("  Code   Fuchs  ", ExperienceLevel.BASICS)
    assert profile.pseudonym == "Code Fuchs"
    restored = StudentProfile.from_dict(profile.to_dict())
    assert restored == profile
    assert restored.experience_label == "Ich kenne die Grundlagen"


@pytest.mark.parametrize("name", ["", "A", "x" * 31])
def test_invalid_pseudonym_is_rejected(name: str) -> None:
    with pytest.raises(ValueError):
        StudentProfile.create(name, ExperienceLevel.FIRST_STEPS)
