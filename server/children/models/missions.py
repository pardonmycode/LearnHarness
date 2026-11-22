"""Missions the teacher assigns."""

from __future__ import annotations

from django.db import models
from learnharness_protocol import Mission, MissionStep

from .common import LearningGroup, mission_id_validator


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
