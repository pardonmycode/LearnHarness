"""Admin: AI settings (provider switch), prompt log and sessions."""

from __future__ import annotations

import json

from django.contrib import admin
from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html

from .models import AiCall, AiSettings, TutorSession


@admin.register(AiSettings)
class AiSettingsAdmin(admin.ModelAdmin):
    formfield_overrides = {models.URLField: {"assume_scheme": "http"}}  # vLLM runs locally
    readonly_fields = ["key_status", "tools", "updated_at"]
    fieldsets = [
        (None, {"fields": ["provider", "key_status", "tools"]}),
        ("Lokales Modell (vLLM)", {"fields": ["vllm_base_url", "vllm_model"]}),
        ("Claude (Anthropic)", {"fields": ["anthropic_model", "anthropic_effort"]}),
        ("ChatGPT (OpenAI)", {"fields": ["openai_model"]}),
        (
            "Harness: Grenzen für die KI",
            {
                "fields": [
                    "max_code_lines_in_chat",
                    "max_changed_lines",
                    "requests_per_minute",
                    "max_output_tokens",
                    "teacher_instructions",
                ]
            },
        ),
        ("Protokoll", {"fields": ["log_prompts", "log_retention_days", "updated_at"]}),
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return not AiSettings.objects.exists()

    def has_delete_permission(self, request: HttpRequest, obj: object = None) -> bool:
        return False

    def changelist_view(self, request: HttpRequest, extra_context: object = None) -> HttpResponse:
        # Only one row: go straight to it.
        AiSettings.load()
        return HttpResponseRedirect(reverse("admin:tutor_aisettings_change", args=[1]))

    @admin.display(description="API-Schlüssel (aus server/.env)")
    def key_status(self, obj: AiSettings) -> str:
        rows = []
        for provider, label in AiSettings.Provider.choices:
            present = bool(AiSettings.api_key(provider))
            if provider == AiSettings.Provider.VLLM:
                state = "gesetzt" if present else "nicht nötig, außer vLLM läuft mit --api-key"
            else:
                state = "gesetzt" if present else "fehlt"
            rows.append(f"{label}: {state}")
        return " · ".join(rows)

    @admin.display(description="Werkzeuge")
    def tools(self, obj: AiSettings) -> str:
        return format_html(
            '<button type="submit" form="lh-test" class="button">Verbindung testen</button> '
            '<a class="button" href="{}">Prompt-Übersicht</a> '
            '<a class="button" href="{}">KI-Protokoll</a>',
            reverse("tutor-prompts"),
            reverse("admin:tutor_aicall_changelist"),
        )

    def render_change_form(
        self, request: HttpRequest, context: dict, *args: object, **kwargs: object
    ) -> HttpResponse:
        # The test button submits a separate small form (forms cannot be nested).
        context["lh_test_url"] = reverse("tutor-test-connection")
        return super().render_change_form(request, context, *args, **kwargs)  # type: ignore[arg-type]


@admin.register(AiCall)
class AiCallAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "child",
        "intent",
        "provider",
        "model",
        "intervened",
        "ok",
        "input_tokens",
        "output_tokens",
        "duration_ms",
    ]
    list_filter = ["intent", "provider", "intervened", "ok", "created_at"]
    search_fields = ["child__pseudonym", "delivered_text", "messages"]
    date_hierarchy = "created_at"
    list_select_related = ["child"]
    readonly_fields = [
        "created_at",
        "child",
        "session",
        "intent",
        "provider",
        "model",
        "ok",
        "error",
        "intervened",
        "notes_display",
        "input_tokens",
        "output_tokens",
        "duration_ms",
        "system_display",
        "messages_display",
        "response_display",
        "delivered_display",
    ]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    ("created_at", "child", "session"),
                    ("intent", "provider", "model"),
                    ("ok", "intervened"),
                    "error",
                    "notes_display",
                    ("input_tokens", "output_tokens", "duration_ms"),
                ]
            },
        ),
        ("Was an die KI ging", {"fields": ["system_display", "messages_display"]}),
        ("Was zurückkam", {"fields": ["response_display", "delivered_display"]}),
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: object = None) -> bool:
        return False

    @staticmethod
    def _pre(text: str) -> str:
        return format_html(
            '<pre style="white-space: pre-wrap; max-height: 30em; overflow: auto">{}</pre>',
            text or "–",
        )

    @admin.display(description="Eingriffe des Harness")
    def notes_display(self, call: AiCall) -> str:
        return "; ".join(call.harness_notes) if call.harness_notes else "keine"

    @admin.display(description="System-Prompt")
    def system_display(self, call: AiCall) -> str:
        return self._pre(call.system_prompt)

    @admin.display(description="Nachrichten")
    def messages_display(self, call: AiCall) -> str:
        parts = [f"[{item.get('role')}]\n{item.get('content')}" for item in call.messages]
        return self._pre("\n\n".join(parts) if parts else json.dumps(call.messages))

    @admin.display(description="Antwort der KI (roh)")
    def response_display(self, call: AiCall) -> str:
        return self._pre(call.response_text)

    @admin.display(description="An das Kind gesendet")
    def delivered_display(self, call: AiCall) -> str:
        return self._pre(call.delivered_text)


@admin.register(TutorSession)
class TutorSessionAdmin(admin.ModelAdmin):
    list_display = ["pseudonym", "child", "project_id", "created_at", "last_activity", "calls"]
    list_filter = ["created_at"]
    search_fields = ["pseudonym", "profile_id"]
    fields = ["pseudonym", "child", "profile_id", "project_id", "created_at", "last_activity"]
    readonly_fields = fields

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: object = None) -> bool:
        return False

    def get_queryset(self, request: HttpRequest) -> QuerySet[TutorSession]:
        return super().get_queryset(request).select_related("child")

    @admin.display(description="KI-Anfragen")
    def calls(self, session: TutorSession) -> str:
        url = reverse("admin:tutor_aicall_changelist") + f"?session__id__exact={session.pk}"
        return format_html('<a href="{}">{}</a>', url, session.aicall_set.count())
