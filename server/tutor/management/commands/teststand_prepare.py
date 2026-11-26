"""Sets up the local test stand: which AI answers and an admin login for this computer."""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser

from tutor.models import AiSettings
from tutor.providers import adopt_first_model

ADMIN_USER = "teststand"
TESTSTAND_REQUESTS_PER_MINUTE = 60  # trying prompts fast must not hit the children's limit


class Command(BaseCommand):
    help = "Richtet den lokalen Teststand ein (KI-Anbieter, Modell, Admin-Zugang)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--provider", choices=["anthropic", "vllm"], required=True)
        # For vLLM it may stay empty: the first model of the server is taken (adopt_first_model).
        parser.add_argument("--model", default="")
        parser.add_argument("--vllm-url", default="")
        parser.add_argument("--effort", default="low")
        parser.add_argument("--admin-password", required=True)

    def handle(self, *args: Any, **options: Any) -> None:
        settings = AiSettings.load()
        settings.provider = options["provider"]
        if options["provider"] == AiSettings.Provider.ANTHROPIC:
            settings.anthropic_model = options["model"]
            settings.anthropic_effort = options["effort"]
        else:
            settings.vllm_model = options["model"] or settings.vllm_model
            settings.vllm_base_url = options["vllm_url"] or settings.vllm_base_url
        settings.log_prompts = True
        settings.requests_per_minute = max(
            settings.requests_per_minute, TESTSTAND_REQUESTS_PER_MINUTE
        )
        settings.save()
        # Also when the stand starts without a test first: take the model vLLM serves.
        adopt_first_model(settings)
        if not settings.active_model:
            raise CommandError("Bitte trage einen Modellnamen ein.")
        user, _ = get_user_model().objects.get_or_create(username=ADMIN_USER)
        user.is_staff = True
        user.is_superuser = True
        user.set_password(options["admin_password"])
        user.save()
        self.stdout.write(f"Teststand bereit: {settings}")
