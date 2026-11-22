"""History of one child and its CSV export."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, time

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.text import slugify

from ..models import Child, ProgressEvent, SkillLevel
from .common import _csv_response, _local


@dataclass(frozen=True)
class Period:
    start: date | None
    end: date | None

    @classmethod
    def from_request(cls, request: HttpRequest) -> Period:
        return cls(_parse_date(request.GET.get("von")), _parse_date(request.GET.get("bis")))

    def filter(self, events: QuerySet[ProgressEvent]) -> QuerySet[ProgressEvent]:
        zone = timezone.get_current_timezone()
        if self.start:
            events = events.filter(recorded_at__gte=datetime.combine(self.start, time.min, zone))
        if self.end:
            events = events.filter(recorded_at__lte=datetime.combine(self.end, time.max, zone))
        return events

    @property
    def query(self) -> str:
        parts = []
        if self.start:
            parts.append(f"von={self.start.isoformat()}")
        if self.end:
            parts.append(f"bis={self.end.isoformat()}")
        return "&".join(parts)


def _parse_date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


@dataclass(frozen=True)
class Step:
    when: datetime
    value: int
    text: str


@dataclass(frozen=True)
class SkillHistory:
    label: str
    steps: list[Step]  # oldest first

    @property
    def current(self) -> Step:
        return self.steps[-1]


def skill_histories(events: list[ProgressEvent]) -> list[SkillHistory]:
    """Group skill events per skill, oldest first; label from the newest entry."""
    by_skill: dict[str, list[ProgressEvent]] = {}
    for event in sorted(events, key=lambda item: (item.recorded_at, item.pk)):
        if event.kind == ProgressEvent.Kind.SKILL:
            by_skill.setdefault(event.item_id, []).append(event)
    histories = [
        SkillHistory(
            label=items[-1].label,
            steps=[
                Step(item.recorded_at, item.value, SkillLevel(item.value).label) for item in items
            ],
        )
        for items in by_skill.values()
    ]
    return sorted(histories, key=lambda history: history.label.lower())


@staff_member_required
def child_history(request: HttpRequest, profile_id: str) -> HttpResponse:
    child = get_object_or_404(Child.objects.select_related("group"), pk=profile_id)
    period = Period.from_request(request)
    events = list(period.filter(child.events.all()))
    context = {
        **admin.site.each_context(request),
        "title": f"Verlauf: {child.pseudonym}",
        "child": child,
        "period": period,
        "skills": child.skills.all(),
        "histories": skill_histories(events),
        "levels_over_time": [e for e in reversed(events) if e.kind == ProgressEvent.Kind.LEVEL],
        "missions_done": [e for e in events if e.kind == ProgressEvent.Kind.MISSION],
        "events": events,
        "levels": SkillLevel.choices,
        "today": timezone.localdate(),
    }
    return render(request, "children/child_history.html", context)


@staff_member_required
def child_history_csv(request: HttpRequest, profile_id: str) -> HttpResponse:
    child = get_object_or_404(Child, pk=profile_id)
    period = Period.from_request(request)
    response = _csv_response(f"verlauf-{slugify(child.pseudonym) or child.pk}.csv")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["Zeitpunkt", "Art", "Bezeichnung", "Stand"])
    for event in reversed(list(period.filter(child.events.all()))):  # oldest first
        if event.kind == ProgressEvent.Kind.SKILL:
            state = SkillLevel(event.value).label
        elif event.kind == ProgressEvent.Kind.LEVEL:
            state = f"Level {event.value}"
        else:
            state = "abgeschlossen"
        writer.writerow([_local(event.recorded_at), event.get_kind_display(), event.label, state])
    return response
