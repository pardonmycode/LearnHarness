"""„Wartende Geräte“: PCs that asked for access, approved or rejected with one click."""

from __future__ import annotations

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db.models import Case, QuerySet, When
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import URLPattern, path, reverse
from django.utils.html import format_html
from django.views.decorators.http import require_POST

from .models import DeviceRequest


@admin.register(DeviceRequest)
class DeviceRequestAdmin(admin.ModelAdmin):
    list_display = ["name", "code_display", "state_display", "created_at", "buttons"]
    list_filter = ["status"]
    readonly_fields = ["name", "code", "status", "created_at", "decided_at", "api_client"]
    fields = readonly_fields
    actions = ["approve_selected", "reject_selected"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False  # only the PC itself can ask

    @admin.display(description="Code")
    def code_display(self, obj: DeviceRequest) -> str:
        return format_html(
            "<strong style='font-size:1.3em;letter-spacing:.15em'>{}</strong>", obj.code
        )  # noqa: E501

    @admin.display(description="Status")
    def state_display(self, obj: DeviceRequest) -> str:
        return "Abgelaufen" if obj.expired else obj.get_status_display()

    @admin.display(description="Freigabe")
    def buttons(self, obj: DeviceRequest) -> str:
        if obj.state != "pending":
            return "–"
        # The buttons send the change list form, which already carries the CSRF token.
        return format_html(
            '<button type="submit" class="button default" formaction="{}">Genehmigen</button> '
            '<button type="submit" class="button" formaction="{}">Ablehnen</button>',
            reverse("admin:children_devicerequest_approve", args=[obj.pk]),
            reverse("admin:children_devicerequest_reject", args=[obj.pk]),
        )

    def get_urls(self) -> list[URLPattern]:
        own = [
            path(
                "<str:request_id>/genehmigen/",
                self.admin_site.admin_view(require_POST(self.approve_view)),
                name="children_devicerequest_approve",
            ),
            path(
                "<str:request_id>/ablehnen/",
                self.admin_site.admin_view(require_POST(self.reject_view)),
                name="children_devicerequest_reject",
            ),
        ]
        return own + super().get_urls()

    def _decide(self, request: HttpRequest, request_id: str, approve: bool) -> HttpResponse:
        if not self.has_change_permission(request):
            raise PermissionDenied
        device = get_object_or_404(DeviceRequest, pk=request_id)
        self._apply(request, device, approve)
        return HttpResponseRedirect(reverse("admin:children_devicerequest_changelist"))

    def approve_view(self, request: HttpRequest, request_id: str) -> HttpResponse:
        return self._decide(request, request_id, approve=True)

    def reject_view(self, request: HttpRequest, request_id: str) -> HttpResponse:
        return self._decide(request, request_id, approve=False)

    def _apply(self, request: HttpRequest, device: DeviceRequest, approve: bool) -> None:
        if approve:
            client = device.approve()
            if client is None:
                self.message_user(
                    request, f"„{device.name}“ ist nicht mehr offen.", messages.WARNING
                )
            else:
                self.message_user(request, f"„{client.name}“ ist jetzt verbunden.")
        elif device.reject():
            self.message_user(request, f"„{device.name}“ wurde abgelehnt.")

    @admin.action(description="Ausgewählte Geräte genehmigen")
    def approve_selected(self, request: HttpRequest, queryset: QuerySet[DeviceRequest]) -> None:
        for device in queryset:
            self._apply(request, device, approve=True)

    @admin.action(description="Ausgewählte Geräte ablehnen")
    def reject_selected(self, request: HttpRequest, queryset: QuerySet[DeviceRequest]) -> None:
        for device in queryset:
            self._apply(request, device, approve=False)

    def get_queryset(self, request: HttpRequest) -> QuerySet[DeviceRequest]:
        # Waiting PCs first, then the newest decisions.
        waiting = Case(When(status=DeviceRequest.Status.PENDING, then=0), default=1)
        return super().get_queryset(request).order_by(waiting, "-created_at")
