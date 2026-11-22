"""Levels, ids and validators shared by the models."""

from __future__ import annotations

import hashlib
from uuid import uuid4

from django.core.validators import RegexValidator
from django.db import models
from learnharness_protocol.missions import MISSION_ID_PATTERN

MIN_LEVEL = 1


MAX_LEVEL = 10


def new_profile_id() -> str:
    return uuid4().hex


class LearningGroup(models.Model):
    name = models.CharField("Name", max_length=60, unique=True)
    note = models.CharField("Notiz", max_length=200, blank=True)

    class Meta:
        verbose_name = "Gruppe"
        verbose_name_plural = "Gruppen"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ExperienceLevel(models.IntegerChoices):
    FIRST_STEPS = 0, "Erste Schritte"
    BASICS = 1, "Grundlagen"
    SOME_PROJECTS = 2, "Einige Projekte"
    INDEPENDENT = 3, "Selbstständig"


class SkillLevel(models.IntegerChoices):
    NOT_STARTED = 0, "Noch nicht begonnen"
    WITH_HELP = 1, "Mit Hilfe"
    ALMOST_INDEPENDENT = 2, "Fast selbstständig"
    CONFIDENT = 3, "Sicher"


def hash_token(token: str) -> str:
    # Tokens are 256-bit random values, so a plain SHA-256 is sufficient (no brute force).
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


mission_id_validator = RegexValidator(
    MISSION_ID_PATTERN, "Nur Kleinbuchstaben, Ziffern, - und _ (z. B. doppelsprung)."
)
