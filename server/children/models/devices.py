"""Device tokens."""

from __future__ import annotations

import secrets

from django.db import models

from .common import hash_token


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
