"""Central data: groups, pseudonymous children, their skills and API access tokens.

Data protection: only pseudonyms are stored. The mapping pseudonym → real child stays
with the teacher (e.g. on paper), not in this database.
"""

from __future__ import annotations

import hashlib
import secrets
from typing import Any
from uuid import uuid4

from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone
from learnharness_protocol import (
    ChildProfile,
    Mission,
    MissionList,
    MissionStep,
    ProgressUpdate,
    Skill,
)
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

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Every change of the level (app, admin form, list editing) lands in the history."""
        previous = (
            None
            if self._state.adding
            else Child.objects.filter(pk=self.pk).values_list("max_level", flat=True).first()
        )
        super().save(*args, **kwargs)
        if previous != self.max_level:
            ProgressEvent.objects.create(
                child=self,
                kind=ProgressEvent.Kind.LEVEL,
                item_id="level",
                label="Level",
                value=self.max_level,
            )

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
        """Start over: skills and history are deleted (data minimisation), level back to 1."""
        self.skills.all().delete()
        self.events.all().delete()
        self.max_level = MIN_LEVEL
        self.save(update_fields=["max_level", "updated_at"])

    def set_skill(self, skill_id: str, label: str, level: int) -> None:
        """Store the current level of a skill; a change is also written to the history."""
        current = self.skills.filter(skill_id=skill_id).first()
        if current is not None and current.level == level and current.label == label:
            return
        SkillProgress.objects.update_or_create(
            child=self, skill_id=skill_id, defaults={"label": label, "level": level}
        )
        if current is None or current.level != level:
            ProgressEvent.objects.create(
                child=self,
                kind=ProgressEvent.Kind.SKILL,
                item_id=skill_id,
                label=label,
                value=level,
            )

    def missions(self) -> MissionList:
        assigned = LearningMission.objects.for_group(self.group).prefetch_related("steps")
        completed = self.events.filter(kind=ProgressEvent.Kind.MISSION).values_list(
            "item_id", flat=True
        )
        return MissionList(
            missions=[mission.to_protocol(with_notes=False) for mission in assigned],
            completed=sorted(set(completed)),
        )

    def complete_mission(self, mission: LearningMission) -> bool:
        """Record a finished mission once; returns False when it was already recorded."""
        _, created = ProgressEvent.objects.get_or_create(
            child=self,
            kind=ProgressEvent.Kind.MISSION,
            item_id=mission.mission_id,
            defaults={"label": mission.title, "value": mission.steps.count()},
        )
        return created

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


class ProgressEvent(models.Model):
    """History: one row per change, so teachers can show the progress over time."""

    class Kind(models.TextChoices):
        SKILL = "skill", "Fähigkeit"
        LEVEL = "level", "Level"
        MISSION = "mission", "Mission"

    child = models.ForeignKey(
        Child, verbose_name="Kind", related_name="events", on_delete=models.CASCADE
    )
    kind = models.CharField("Art", max_length=10, choices=Kind.choices)
    item_id = models.CharField("ID", max_length=64)
    label = models.CharField("Bezeichnung", max_length=120)
    # skill: 0–3 (SkillLevel), level: 1–10, mission: number of steps
    value = models.PositiveSmallIntegerField("Wert")
    recorded_at = models.DateTimeField("Zeitpunkt", default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "Verlaufseintrag"
        verbose_name_plural = "Verlauf"
        ordering = ["-recorded_at", "-pk"]
        indexes = [models.Index(fields=["child", "kind", "item_id"], name="event_child_item")]

    def __str__(self) -> str:
        return f"{self.child}: {self.describe()}"

    def describe(self) -> str:
        if self.kind == self.Kind.SKILL:
            return f"{self.label}: {SkillLevel(self.value).label}"
        if self.kind == self.Kind.LEVEL:
            return f"Level {self.value}"
        return f"Mission „{self.label}“ abgeschlossen"


mission_id_validator = RegexValidator(
    MISSION_ID_PATTERN, "Nur Kleinbuchstaben, Ziffern, - und _ (z. B. doppelsprung)."
)


class LearningMissionQuerySet(models.QuerySet["LearningMission"]):
    def for_group(self, group: LearningGroup | None) -> LearningMissionQuerySet:
        """Active missions for everyone plus those assigned to this group."""
        everyone = models.Q(groups__isnull=True)
        if group is not None:
            everyone |= models.Q(groups=group)
        ids = self.filter(everyone).values("pk")
        return self.filter(pk__in=ids, active=True)


class LearningMission(models.Model):
    mission_id = models.CharField(
        "Kennung",
        max_length=64,
        unique=True,
        validators=[mission_id_validator],
        help_text="Feste ID für App und Lernserver, z. B. doppelsprung. Später nicht ändern.",
    )
    title = models.CharField("Titel", max_length=120)
    goal = models.TextField("Ziel (für das Kind)", help_text="z. B. Baue einen Doppelsprung!")
    skill = models.CharField(
        "Fähigkeit (ID)", max_length=64, blank=True, help_text="Optional, z. B. conditions"
    )
    groups = models.ManyToManyField(
        LearningGroup,
        verbose_name="Gruppen",
        related_name="missions",
        blank=True,
        help_text="Leer lassen = für alle Gruppen.",
    )
    active = models.BooleanField("Aktiv", default=True)
    position = models.PositiveSmallIntegerField("Reihenfolge", default=0)
    created_at = models.DateTimeField("Angelegt", auto_now_add=True)

    objects = LearningMissionQuerySet.as_manager()

    class Meta:
        verbose_name = "Mission"
        verbose_name_plural = "Missionen"
        ordering = ["position", "title"]

    def __str__(self) -> str:
        return self.title

    def to_protocol(self, *, with_notes: bool) -> Mission:
        return Mission(
            id=self.mission_id,
            title=self.title,
            goal=self.goal,
            skill=self.skill or None,
            steps=[
                MissionStep(
                    id=step.step_id,
                    title=step.title,
                    kind=step.kind,  # type: ignore[arg-type]  # choices match MissionStepKind
                    note=(step.note or None) if with_notes else None,
                )
                for step in self.steps.all()
            ],
        )


class LearningMissionStep(models.Model):
    class Kind(models.TextChoices):
        UNDERSTAND = "understand", "Verstehen (Erklärung + Frage)"
        LEARN = "learn", "Lernen (neues Konzept + kleine Übung)"
        EXERCISE = "exercise", "Üben (Code ergänzen, danach wird Code geschrieben)"
        TRY = "try", "In Godot ausprobieren (bestätigt das Kind)"

    mission = models.ForeignKey(
        LearningMission, verbose_name="Mission", related_name="steps", on_delete=models.CASCADE
    )
    step_id = models.CharField("Kennung", max_length=64, validators=[mission_id_validator])
    title = models.CharField("Schritt (für das Kind)", max_length=200)
    kind = models.CharField("Art", max_length=20, choices=Kind.choices)
    note = models.TextField(
        "Hinweis für den Lernserver",
        blank=True,
        max_length=1000,
        help_text="Für das Kind unsichtbar, z. B. welche Übung oder was betont werden soll.",
    )
    position = models.PositiveSmallIntegerField("Reihenfolge", default=0)

    class Meta:
        verbose_name = "Schritt"
        verbose_name_plural = "Schritte"
        ordering = ["position", "pk"]
        constraints = [
            models.UniqueConstraint(fields=["mission", "step_id"], name="unique_mission_step"),
        ]

    def __str__(self) -> str:
        return self.title
