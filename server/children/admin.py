"""Teacher administration: groups, children, skills and API access tokens."""

from __future__ import annotations

import secrets

from django.contrib import admin, messages
from django.db.models import Count, Q, QuerySet
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html

from .models import ApiClient, Child, LearningGroup, SkillProgress, hash_token


class SkillProgressInline(admin.TabularInline):
    model = SkillProgress
    extra = 0
    fields = ["label", "skill_id", "level", "updated_at"]
    readonly_fields = ["updated_at"]


class ChildInline(admin.TabularInline):
    model = Child
    extra = 0
    fields = ["pseudonym", "experience_level", "max_level", "active"]
    show_change_link = True


@admin.register(LearningGroup)
class LearningGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "note", "child_count", "overview_link"]
    search_fields = ["name"]
    inlines = [ChildInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet[LearningGroup]:
        return (
            super()
            .get_queryset(request)
            .annotate(active_children=Count("children", filter=Q(children__active=True)))
        )

    @admin.display(description="Kinder", ordering="active_children")
    def child_count(self, group: LearningGroup) -> int:
        return group.active_children

    @admin.display(description="Übersicht")
    def overview_link(self, group: LearningGroup) -> str:
        return format_html('<a href="{}">Übersicht</a>', reverse("overview-group", args=[group.pk]))


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = [
        "pseudonym",
        "group",
        "experience_level",
        "max_level",
        "active",
        "last_seen_at",
    ]
    list_editable = ["max_level", "group"]
    list_filter = ["active", "group", "experience_level", "max_level"]
    search_fields = ["pseudonym", "profile_id"]
    readonly_fields = ["profile_id", "created_at", "updated_at", "last_seen_at"]
    fieldsets = [
        (None, {"fields": ["pseudonym", "group", "experience_level", "max_level", "active"]}),
        ("Technisch", {"fields": ["profile_id", "created_at", "updated_at", "last_seen_at"]}),
    ]
    inlines = [SkillProgressInline]
    actions = ["unlock_next_level", "reset_learning", "archive", "reactivate"]

    @admin.action(description="Nächstes Level freischalten")
    def unlock_next_level(self, request: HttpRequest, queryset: QuerySet[Child]) -> None:
        for child in queryset:
            child.unlock(child.max_level + 1)
        self.message_user(request, f"{queryset.count()} Kind(er): nächstes Level freigeschaltet.")

    @admin.action(description="Fortschritt zurücksetzen (Level 1, Fähigkeiten löschen)")
    def reset_learning(self, request: HttpRequest, queryset: QuerySet[Child]) -> None:
        for child in queryset:
            child.reset_learning()
        self.message_user(request, f"{queryset.count()} Kind(er) zurückgesetzt.")

    @admin.action(description="Archivieren (nicht mehr in der App anzeigen)")
    def archive(self, request: HttpRequest, queryset: QuerySet[Child]) -> None:
        count = queryset.update(active=False)
        self.message_user(request, f"{count} Kind(er) archiviert.")

    @admin.action(description="Wieder aktivieren")
    def reactivate(self, request: HttpRequest, queryset: QuerySet[Child]) -> None:
        count = queryset.update(active=True)
        self.message_user(request, f"{count} Kind(er) wieder aktiv.")


@admin.register(ApiClient)
class ApiClientAdmin(admin.ModelAdmin):
    list_display = ["name", "kind", "active", "created_at", "last_used_at"]
    list_filter = ["kind", "active"]
    fields = ["name", "kind", "active", "created_at", "last_used_at"]
    readonly_fields = ["created_at", "last_used_at"]
    actions = ["rotate_token"]

    def save_model(self, request: HttpRequest, obj: ApiClient, form: object, change: bool) -> None:
        token = None
        if not change:
            token = secrets.token_urlsafe(32)
            obj.token_hash = hash_token(token)
        super().save_model(request, obj, form, change)
        if token:
            self._show_token(request, obj, token)

    @admin.action(description="Neuen Token erzeugen (alter wird ungültig)")
    def rotate_token(self, request: HttpRequest, queryset: QuerySet[ApiClient]) -> None:
        for client in queryset:
            self._show_token(request, client, client.rotate())

    def _show_token(self, request: HttpRequest, client: ApiClient, token: str) -> None:
        self.message_user(
            request,
            f"Token für „{client.name}“ (wird nur jetzt angezeigt): {token}",
            messages.WARNING,
        )
