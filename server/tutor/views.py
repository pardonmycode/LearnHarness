"""Staff pages: which prompts go out to the AI, and a connection test."""

from __future__ import annotations

import json

from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from learnharness_protocol import StudentMessage

from . import harness
from .models import AiSettings
from .providers import connection_problem, model_available

INTENT_LABELS = {
    "chat": "Tutor-Chat",
    "hint": "Hinweis zur Aufgabe",
    "explain": "Code verstehen",
    "learn": "LearnAgent-Runde",
    "mission": "Mission aus einem Wunsch planen",
    "mission_step": "Missionsschritt",
    "project_plan": "Projekt und To-do-Liste planen",
    "review": "Code-Abgabe prüfen",
}
SCHEMAS = {
    "explain": harness.EXERCISE_SCHEMA,
    "learn": harness.EXERCISE_SCHEMA,
    "mission_step": harness.EXERCISE_SCHEMA,
    "mission": harness.MISSION_SCHEMA,
    "project_plan": harness.PROJECT_PLAN_SCHEMA,
    "review": harness.REVIEW_SCHEMA,
}
EXAMPLE_CODE = "extends CharacterBody2D\n\nvar speed = 200\n"


def _int(value: str | None, default: int, low: int, high: int) -> int:
    try:
        return max(low, min(high, int(value or default)))
    except ValueError:
        return default


@staff_member_required
def prompt_overview(request: HttpRequest) -> HttpResponse:
    settings = AiSettings.load()
    level = _int(request.GET.get("stufe"), 3, 1, 10)
    experience = _int(request.GET.get("erfahrung"), 1, 0, 3)
    example = StudentMessage(
        intent="learn",
        session_id="beispiel",
        project_id="beispiel",
        learning_level=level,
        experience_level=experience,
        file="player.gd",
        code_excerpt=EXAMPLE_CODE,
        excerpt_start_line=1,
        message="Meine Figur soll springen können",
    )
    intents = []
    for intent, label in INTENT_LABELS.items():
        system = harness.system_prompt(
            intent,
            settings,
            learning_level=level if intent in ("learn", "chat") else None,
            experience_level=experience,
            hint_level=2,
            game=True,
        )
        if intent in ("learn", "explain", "mission_step"):
            system += "\n\n" + harness.EXERCISE_FORMAT_HELP
        schema = SCHEMAS.get(intent)
        intents.append(
            {
                "key": intent,
                "label": label,
                "system": system,
                "schema": json.dumps(schema, ensure_ascii=False, indent=2) if schema else "",
            }
        )
    context = {
        **admin.site.each_context(request),
        "title": "Prompt-Übersicht",
        "settings": settings,
        "intents": intents,
        "example_user": harness.user_prompt(example),
        "level": level,
        "experience": experience,
        "levels": range(1, 11),
        "experiences": sorted(harness.EXPERIENCE.items()),
        "replacement": harness.REPLACEMENT.strip(),
    }
    return render(request, "tutor/prompts.html", context)


@staff_member_required
@require_POST
def test_connection(request: HttpRequest) -> HttpResponse:
    settings = AiSettings.load()
    ok, latency = model_available(force=True)
    problem = connection_problem(settings)
    if problem:
        messages.error(request, f"{settings.get_provider_display()}: {problem}")
    elif ok:
        messages.success(
            request,
            f"{settings.get_provider_display()} mit „{settings.active_model}“ erreichbar "
            f"({latency} ms).",
        )
    else:
        messages.error(
            request,
            f"{settings.get_provider_display()} mit „{settings.active_model or '–'}“ nicht "
            "erreichbar. Adresse, Modellname und API-Schlüssel in server/.env prüfen.",
        )
    return redirect(reverse("admin:tutor_aisettings_change", args=[1]))
