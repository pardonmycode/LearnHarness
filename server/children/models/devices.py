"""Device tokens and PCs waiting for approval."""

from __future__ import annotations

import secrets
from datetime import timedelta

from django.db import models, transaction
from django.utils import timezone

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


REQUEST_LIFETIME = timedelta(minutes=15)
MAX_PENDING_REQUESTS = 20


def new_request_code() -> str:
    return f"{secrets.randbelow(10_000):04d}"


def new_request_id() -> str:
    return secrets.token_hex(16)


class DeviceRequest(models.Model):
    """A PC asking for access; it becomes an ApiClient when a teacher approves it."""

    class Status(models.TextChoices):
        PENDING = "pending", "Wartet"
        APPROVED = "approved", "Genehmigt"
        REJECTED = "rejected", "Abgelehnt"

    id = models.CharField(primary_key=True, max_length=32, default=new_request_id)
    name = models.CharField("Name", max_length=40)
    code = models.CharField("Code", max_length=4, default=new_request_code)
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    status = models.CharField(
        "Status", max_length=10, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField("Angefragt", auto_now_add=True)
    decided_at = models.DateTimeField("Entschieden", null=True, blank=True)
    api_client = models.ForeignKey(
        ApiClient, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Zugang"
    )

    class Meta:
        verbose_name = "Wartendes Gerät"
        verbose_name_plural = "Wartende Geräte"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} (Code {self.code})"

    @property
    def expired(self) -> bool:
        return (
            self.status == self.Status.PENDING
            and timezone.now() - self.created_at > REQUEST_LIFETIME
        )

    @property
    def state(self) -> str:
        """What the PC is told: pending, approved, rejected or expired."""
        return "expired" if self.expired else str(self.status)

    @transaction.atomic
    def approve(self) -> ApiClient | None:
        """Turns the request into a device access; None if it is no longer open."""
        if self.status != self.Status.PENDING or self.expired:
            return None
        name, number = self.name, 2
        while ApiClient.objects.filter(name=name).exists():
            name, number = f"{self.name} ({number})", number + 1
        client = ApiClient.objects.create(
            name=name, kind=ApiClient.Kind.CLIENT, token_hash=self.token_hash
        )
        self.status, self.api_client, self.decided_at = self.Status.APPROVED, client, timezone.now()
        self.save(update_fields=["status", "api_client", "decided_at"])
        return client

    def reject(self) -> bool:
        if self.status != self.Status.PENDING:
            return False
        self.status, self.decided_at = self.Status.REJECTED, timezone.now()
        self.save(update_fields=["status", "decided_at"])
        return True
