"""A child with skills and history."""

from __future__ import annotations

from typing import Any

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from learnharness_protocol import ChildProfile, MissionList, ProgressUpdate, Skill

from .common import MAX_LEVEL, MIN_LEVEL, ExperienceLevel, LearningGroup, SkillLevel, new_profile_id
from .missions import LearningMission


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
