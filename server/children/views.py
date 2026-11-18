"""Teacher pages: group overview, history per child and CSV exports (staff only)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, time

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Prefetch, QuerySet
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify

from .models import Child, LearningGroup, ProgressEvent, SkillLevel, SkillProgress

# Selector values besides a group id.
ALL = "alle"
UNGROUPED = "ohne-gruppe"


@dataclass(frozen=True)
class Column:
    skill_id: str
    label: str


@dataclass(frozen=True)
class Row:
    child: Child
    cells: list[SkillProgress | None]


def build_table(children: list[Child]) -> tuple[list[Column], list[Row]]:
    """Columns are all skills of these children (by id, sorted by label); cells may be empty."""
    labels: dict[str, str] = {}
    for child in children:
        for item in child.skills.all():
            labels.setdefault(item.skill_id, item.label)
    columns = [
        Column(skill_id, label)
        for skill_id, label in sorted(labels.items(), key=lambda pair: (pair[1].lower(), pair[0]))
    ]
    rows = []
    for child in children:
        by_id = {item.skill_id: item for item in child.skills.all()}
        rows.append(Row(child, [by_id.get(column.skill_id) for column in columns]))
    return columns, rows


@dataclass(frozen=True)
class Selection:
    children: QuerySet[Child]
    group: LearningGroup | None
    title: str


def _select(selection: str) -> Selection:
    children = (
        Child.objects.filter(active=True)
        .select_related("group")
        .prefetch_related(
            Prefetch(
                "skills",
                queryset=SkillProgress.objects.only("child_id", "skill_id", "label", "level"),
            )
        )
    )
    if selection == UNGROUPED:
        return Selection(children.filter(group__isnull=True), None, "Übersicht: ohne Gruppe")
    if selection == ALL:
        return Selection(children, None, "Übersicht: alle Gruppen")
    if not selection.isdigit():
        raise Http404
    group = get_object_or_404(LearningGroup, pk=int(selection))
    return Selection(children.filter(group=group), group, f"Übersicht: {group.name}")


@staff_member_required
def overview(request: HttpRequest, selection: str = ALL) -> HttpResponse:
    chosen = request.GET.get("gruppe")
    if chosen is not None:
        # The group selector submits ?gruppe=…; turn it into a clean, bookmarkable URL.
        if chosen.isdigit() or chosen == UNGROUPED:
            return redirect("overview-group", selection=chosen)
        return redirect("overview")
    if selection not in (ALL, UNGROUPED) and not selection.isdigit():
        return redirect("overview")

    chosen_selection = _select(selection)
    columns, rows = build_table(list(chosen_selection.children.order_by("pseudonym")))
    context = {
        **admin.site.each_context(request),
        "title": chosen_selection.title,
        "groups": LearningGroup.objects.all(),
        "selection": selection,
        "selected_group": chosen_selection.group,
        "all_value": ALL,
        "ungrouped_value": UNGROUPED,
        "show_group": selection == ALL,
        "columns": columns,
        "rows": rows,
        "levels": SkillLevel.choices,
    }
    return render(request, "children/overview.html", context)


# CSV ----------------------------------------------------------------------------------


def _csv_response(filename: str) -> HttpResponse:
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    # BOM + semicolon: German Excel opens the file with umlauts and columns intact.
    response.write("﻿")
    return response


def _local(moment: datetime | None) -> str:
    return timezone.localtime(moment).strftime("%d.%m.%Y %H:%M") if moment else ""


@staff_member_required
def overview_csv(request: HttpRequest, selection: str = ALL) -> HttpResponse:
    chosen = _select(selection)
    columns, rows = build_table(list(chosen.children.order_by("pseudonym")))
    name = chosen.group.name if chosen.group else selection
    response = _csv_response(f"uebersicht-{slugify(name) or 'gruppe'}.csv")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(
        ["Spitzname", "Gruppe", "Level", "Zuletzt gesehen", *[c.label for c in columns]]
    )
    for row in rows:
        writer.writerow(
            [
                row.child.pseudonym,
                row.child.group.name if row.child.group else "",
                row.child.max_level,
                _local(row.child.last_seen_at),
                *[cell.get_level_display() if cell else "" for cell in row.cells],
            ]
        )
    return response


# History per child ------------------------------------------------------------------


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
