from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from children.models import ApiClient


class Command(BaseCommand):
    help = "Legt einen API-Zugang an und zeigt den Token einmalig an."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("name", help="z. B. 'PC Raum 12' oder 'Lernserver'")
        parser.add_argument(
            "--kind",
            choices=[choice.value for choice in ApiClient.Kind],
            default=ApiClient.Kind.CLIENT,
        )

    def handle(self, *args: Any, **options: Any) -> None:
        name = options["name"]
        if ApiClient.objects.filter(name=name).exists():
            raise CommandError(f"Es gibt schon einen Zugang namens „{name}“.")
        client, token = ApiClient.issue(name, options["kind"])
        self.stdout.write(f"Zugang „{client.name}“ ({client.get_kind_display()}) angelegt.")
        self.stdout.write("Token (wird nur jetzt angezeigt):")
        self.stdout.write(token)
