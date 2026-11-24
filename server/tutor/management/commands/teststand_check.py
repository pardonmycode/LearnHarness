"""Checks whether the AI of the test stand answers; the reason is printed in plain words."""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError

from tutor.models import AiSettings
from tutor.providers import ProviderError, connection_problem, get_provider


class Command(BaseCommand):
    help = "Prüft die Verbindung zur eingestellten KI."

    def handle(self, *args: Any, **options: Any) -> None:
        settings = AiSettings.load()
        problem = connection_problem(settings)
        if problem:
            raise CommandError(problem)
        try:
            reachable = get_provider(settings).ping()
        except ProviderError as exc:
            raise CommandError(str(exc)) from exc
        if not reachable:
            raise CommandError(
                f"Keine Antwort von {settings.get_provider_display()} mit dem Modell "
                f"„{settings.active_model}“. Stimmen Adresse und Modellname?"
            )
        self.stdout.write(f"Verbindung klappt: {settings.active_model}")
