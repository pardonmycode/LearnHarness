"""Central data: groups, pseudonymous children, their skills and API access tokens.

Data protection: only pseudonyms are stored. The mapping pseudonym → real child stays
with the teacher (e.g. on paper), not in this database.
"""

from __future__ import annotations

import hashlib
import secrets
from uuid import uuid4

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from learnharness_protocol import ChildProfile, ProgressUpdate, Skill

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


class Child(models.Model):
    profile_id = models.CharField(
        "Profil-ID", primary_key=True, max_length=32, default=new_profile_id, editable=False
    )
    pseudonym = models.CharField("Spitzname", max_length=30)
    experience_level = models.PositiveSmallIntegerField(
        "Vorkenntnisse", choices=ExperienceLevel.choices, default=ExperienceLevel.FIRST_STEPS
    )
    max_level = models.PositiveSmallIntegerField(
        "Freigeschaltetes Level",
        default=MIN_LEVEL,
        validators=[MinValueValidator(MIN_LEVEL), MaxValueValidator(MAX_LEVEL)],
    )
    group = models.ForeignKey(
        LearningGroup,
        verbose_name="Gruppe",
        related_name="children",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    active = models.BooleanField(
        "Aktiv", default=True, help_text="Archivierte Kinder erscheinen nicht mehr in der App."
    )
    created_at = models.DateTimeField("Angelegt", auto_now_add=True)
    updated_at = models.DateTimeField("Geändert", auto_now=True)
    last_seen_at = models.DateTimeField("Zuletzt gesehen", null=True, blank=True)

    class Meta:
        verbose_name = "Kind"
        verbose_name_plural = "Kinder"
        ordering = ["pseudonym"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(max_level__gte=MIN_LEVEL, max_level__lte=MAX_LEVEL),
                name="child_max_level_range",
            ),
            models.CheckConstraint(
                condition=models.Q(experience_level__lte=ExperienceLevel.INDEPENDENT),
                name="child_experience_level_range",
            ),
        ]

    def __str__(self) -> str:
        return self.pseudonym

    def to_protocol(self) -> ChildProfile:
        return ChildProfile(
            profile_id=self.profile_id,
            pseudonym=self.pseudonym,
            experience_level=self.experience_level,
            max_level=self.max_level,
            group=self.group.name if self.group else None,
        )

    def progress(self) -> ProgressUpdate:
        return ProgressUpdate(
            skills=[
                Skill(id=item.skill_id, label=item.label, level=item.level)
                for item in self.skills.all()
            ]
        )

    def unlock(self, level: int) -> None:
        """Raise the level (never lowers it; lowering is done by teachers in the admin)."""
        target = max(MIN_LEVEL, min(MAX_LEVEL, level))
        if target > self.max_level:
            self.max_level = target
            self.save(update_fields=["max_level", "updated_at"])

    def reset_learning(self) -> None:
        self.skills.all().delete()
        self.max_level = MIN_LEVEL
        self.save(update_fields=["max_level", "updated_at"])

    def touch(self) -> None:
        Child.objects.filter(pk=self.pk).update(last_seen_at=timezone.now())


class SkillLevel(models.IntegerChoices):
    NOT_STARTED = 0, "Noch nicht begonnen"
    WITH_HELP = 1, "Mit Hilfe"
    ALMOST_INDEPENDENT = 2, "Fast selbstständig"
    CONFIDENT = 3, "Sicher"


class SkillProgress(models.Model):
    child = models.ForeignKey(
        Child, verbose_name="Kind", related_name="skills", on_delete=models.CASCADE
    )
    skill_id = models.CharField("Fähigkeit (ID)", max_length=64)
    label = models.CharField("Fähigkeit", max_length=120)
    level = models.PositiveSmallIntegerField("Stand", choices=SkillLevel.choices)
    updated_at = models.DateTimeField("Geändert", auto_now=True)

    class Meta:
        verbose_name = "Fähigkeit"
        verbose_name_plural = "Fähigkeiten"
        ordering = ["label"]
        constraints = [
            models.UniqueConstraint(fields=["child", "skill_id"], name="unique_child_skill"),
        ]

    def __str__(self) -> str:
        return f"{self.label}: {self.get_level_display()}"


def hash_token(token: str) -> str:
    # Tokens are 256-bit random values, so a plain SHA-256 is sufficient (no brute force).
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class ApiClient(models.Model):
    class Kind(models.TextChoices):
        CLIENT = "client", "Lern-App (PC im Raum)"
        LEARNSERVER = "learnserver", "Lernserver (KI)"

    name = models.CharField("Name", max_length=80, unique=True)
    kind = models.CharField("Art", max_length=20, choices=Kind.choices, default=Kind.CLIENT)
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    active = models.BooleanField("Aktiv", default=True)
    created_at = models.DateTimeField("Angelegt", auto_now_add=True)
    last_used_at = models.DateTimeField("Zuletzt benutzt", null=True, blank=True)

    class Meta:
        verbose_name = "API-Zugang"
        verbose_name_plural = "API-Zugänge"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_kind_display()})"

    @classmethod
    def issue(cls, name: str, kind: str = Kind.CLIENT) -> tuple[ApiClient, str]:
        """Create an access and return the plain token. It is shown exactly once."""
        token = secrets.token_urlsafe(32)
        client = cls.objects.create(name=name, kind=kind, token_hash=hash_token(token))
        return client, token

    def rotate(self) -> str:
        token = secrets.token_urlsafe(32)
        self.token_hash = hash_token(token)
        self.save(update_fields=["token_hash"])
        return token
