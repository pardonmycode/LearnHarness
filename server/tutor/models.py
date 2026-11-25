"""The built-in learning server: AI settings, tutor sessions, exercises and the prompt log."""

from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

from django.db import models
from django.utils import timezone

from children.models import ApiClient, Child


class AiSettings(models.Model):
    """One row (pk=1) that the teacher edits in the admin: which AI answers the children."""

    class Provider(models.TextChoices):
        VLLM = "vllm", "Lokales Modell (vLLM)"
        ANTHROPIC = "anthropic", "Claude (Anthropic)"
        OPENAI = "openai", "ChatGPT (OpenAI)"

    class Effort(models.TextChoices):
        DEFAULT = "", "Standard des Modells"
        LOW = "low", "niedrig (schnell, günstig)"
        MEDIUM = "medium", "mittel"
        HIGH = "high", "hoch"

    provider = models.CharField(
        "Aktiver Anbieter", max_length=20, choices=Provider.choices, default=Provider.VLLM
    )
    vllm_base_url = models.URLField(
        "vLLM-Adresse",
        default="http://localhost:8001/v1",
        help_text="OpenAI-kompatible Adresse des vLLM-Servers, endet meist auf /v1.",
    )
    vllm_model = models.CharField(
        "vLLM-Modell",
        max_length=200,
        blank=True,
        help_text="Name wie beim Start von vLLM angegeben (z. B. Qwen/Qwen2.5-Coder-14B-Instruct).",
    )
    anthropic_model = models.CharField("Claude-Modell", max_length=100, default="claude-opus-5-5")
    anthropic_effort = models.CharField(
        "Claude: Denkaufwand",
        max_length=10,
        choices=Effort.choices,
        default=Effort.LOW,
        blank=True,
        help_text="Für kurze Antworten an Kinder reicht meist „niedrig“.",
    )
    openai_model = models.CharField(
        "ChatGPT-Modell",
        max_length=100,
        blank=True,
        help_text="Modellname aus der OpenAI-Plattform.",
    )
    max_output_tokens = models.PositiveIntegerField(
        "Höchstlänge einer Antwort (Tokens)", default=4000
    )
    max_code_lines_in_chat = models.PositiveSmallIntegerField(
        "Höchstens so viele Codezeilen am Stück in Tutor-Antworten",
        default=3,
        help_text="Längere Codeblöcke werden durch einen Hinweis ersetzt (keine fertigen "
        "Lösungen).",
    )
    max_changed_lines = models.PositiveSmallIntegerField(
        "Höchstens so viele geänderte Zeilen schreibt der LearnAgent nach einer richtigen Antwort",
        default=12,
    )
    requests_per_minute = models.PositiveSmallIntegerField(
        "Anfragen pro Kind und Minute", default=12, help_text="Schützt vor hohen Kosten."
    )
    teacher_instructions = models.TextField(
        "Zusätzliche Anweisungen an die KI",
        blank=True,
        help_text="Werden an die festen Regeln angehängt, z. B. „Wir benutzen Godot 4.3“. "
        "Die festen Regeln (keine fertigen Lösungen) lassen sich hier nicht aufheben.",
    )
    log_prompts = models.BooleanField(
        "Prompts und Antworten protokollieren",
        default=True,
        help_text="Für die Übersicht „KI-Protokoll“. Enthält, was die Kinder schreiben.",
    )
    log_retention_days = models.PositiveSmallIntegerField(
        "Protokoll aufbewahren (Tage)", default=30
    )
    updated_at = models.DateTimeField("Geändert", auto_now=True)

    class Meta:
        verbose_name = "KI-Einstellungen"
        verbose_name_plural = "KI-Einstellungen"

    def __str__(self) -> str:
        return f"KI: {self.get_provider_display()} ({self.active_model or 'kein Modell'})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.pk = 1  # singleton
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> AiSettings:
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings

    @property
    def active_model(self) -> str:
        return {
            self.Provider.VLLM: self.vllm_model,
            self.Provider.ANTHROPIC: self.anthropic_model,
            self.Provider.OPENAI: self.openai_model,
        }.get(self.provider, "")

    @staticmethod
    def api_key(provider: str) -> str:
        """Keys only come from the environment (server/.env), never from the database."""
        name = {
            AiSettings.Provider.VLLM: "VLLM_API_KEY",
            AiSettings.Provider.ANTHROPIC: "ANTHROPIC_API_KEY",
            AiSettings.Provider.OPENAI: "OPENAI_API_KEY",
        }.get(provider, "")
        return os.environ.get(name, "").strip() if name else ""


def new_session_id() -> str:
    return uuid4().hex


class TutorSession(models.Model):
    id = models.CharField(primary_key=True, max_length=32, default=new_session_id, editable=False)
    child = models.ForeignKey(
        Child, verbose_name="Kind", null=True, blank=True, on_delete=models.SET_NULL
    )
    profile_id = models.CharField("Profil-ID", max_length=64)
    pseudonym = models.CharField("Spitzname", max_length=30)
    experience_level = models.PositiveSmallIntegerField("Vorkenntnisse", default=0)
    project_id = models.CharField("Projekt", max_length=200)
    api_client = models.ForeignKey(
        ApiClient, verbose_name="Gerät", null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField("Begonnen", auto_now_add=True)
    last_activity = models.DateTimeField("Zuletzt aktiv", default=timezone.now)
    # task id -> hint level already given; recent chat turns; missions planned from wishes
    hint_levels = models.JSONField(default=dict, blank=True)
    history = models.JSONField(default=list, blank=True)
    wish_missions = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Lernsitzung"
        verbose_name_plural = "Lernsitzungen"
        ordering = ["-last_activity"]

    def __str__(self) -> str:
        return f"{self.pseudonym} ({self.created_at:%d.%m.%Y %H:%M})"


class ExerciseRecord(models.Model):
    """An exercise as sent to the child plus what only the server knows: the answers and the
    code that is released after a correct answer."""

    id = models.CharField(primary_key=True, max_length=64)
    session = models.ForeignKey(TutorSession, related_name="exercises", on_delete=models.CASCADE)
    intent = models.CharField(max_length=20)
    skill_id = models.CharField(max_length=64)
    exercise = models.JSONField()
    answers = models.JSONField()
    explanation = models.TextField(blank=True)
    generated_path = models.CharField(max_length=500, blank=True)
    generated_content = models.TextField(blank=True)
    # Checked changes to the Godot scene; like the code they go out after a correct answer.
    scene_path = models.CharField(max_length=500, blank=True)
    scene_changes = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    solved_at = models.DateTimeField(null=True, blank=True)
    wrong_attempts = models.PositiveSmallIntegerField(default=0)  # before it was solved

    class Meta:
        verbose_name = "Übung"
        verbose_name_plural = "Übungen"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.id


class AiCall(models.Model):
    """One request to the AI: what went out, what came back and what the harness changed."""

    created_at = models.DateTimeField("Zeitpunkt", auto_now_add=True, db_index=True)
    session = models.ForeignKey(
        TutorSession, verbose_name="Sitzung", null=True, blank=True, on_delete=models.SET_NULL
    )
    child = models.ForeignKey(
        Child, verbose_name="Kind", null=True, blank=True, on_delete=models.SET_NULL
    )
    intent = models.CharField("Zweck", max_length=20)
    provider = models.CharField("Anbieter", max_length=20)
    model = models.CharField("Modell", max_length=200)
    system_prompt = models.TextField("System-Prompt")
    messages = models.JSONField("Nachrichten", default=list)
    response_text = models.TextField("Antwort der KI", blank=True)
    delivered_text = models.TextField("An das Kind gesendet", blank=True)
    harness_notes = models.JSONField("Eingriffe des Harness", default=list, blank=True)
    intervened = models.BooleanField("Harness hat eingegriffen", default=False)
    input_tokens = models.PositiveIntegerField("Tokens rein", null=True, blank=True)
    output_tokens = models.PositiveIntegerField("Tokens raus", null=True, blank=True)
    duration_ms = models.PositiveIntegerField("Dauer (ms)", null=True, blank=True)
    ok = models.BooleanField("Erfolgreich", default=True)
    error = models.TextField("Fehler", blank=True)

    class Meta:
        verbose_name = "KI-Anfrage"
        verbose_name_plural = "KI-Protokoll"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.created_at:%d.%m.%Y %H:%M} {self.intent} ({self.provider})"
