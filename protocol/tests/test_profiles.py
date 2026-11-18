from __future__ import annotations

from uuid import uuid4

import pytest
from learnharness_protocol import ChildProfile, ChildProfileUpdate, LevelUnlock
from pydantic import ValidationError


def test_child_profile_normalizes_pseudonym_and_defaults_level() -> None:
    profile = ChildProfile(
        profile_id=uuid4().hex, pseudonym="  Roter  Fuchs ", experience_level=0
    )
    assert profile.pseudonym == "Roter Fuchs"
    assert profile.max_level == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"profile_id": "kein-hex"},
        {"pseudonym": "x"},
        {"experience_level": 4},
        {"max_level": 11},
        {"real_name": "Anna Muster"},  # real names are not part of the protocol
    ],
)
def test_child_profile_rejects_invalid_data(changes: dict[str, object]) -> None:
    data: dict[str, object] = {
        "profile_id": uuid4().hex,
        "pseudonym": "Fuchs",
        "experience_level": 1,
    }
    data.update(changes)
    with pytest.raises(ValidationError):
        ChildProfile.model_validate(data)


def test_update_and_unlock_validate_ranges() -> None:
    assert ChildProfileUpdate(pseudonym=" Eule ").pseudonym == "Eule"
    assert ChildProfileUpdate().pseudonym is None
    with pytest.raises(ValidationError):
        LevelUnlock(level=0)
