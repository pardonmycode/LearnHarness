"""Tables, group selection and CSV helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.db.models import Prefetch, QuerySet
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from ..models import Child, LearningGroup, SkillProgress

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


def _csv_response(filename: str) -> HttpResponse:
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    # BOM + semicolon: German Excel opens the file with umlauts and columns intact.
    response.write("﻿")
    return response


def _local(moment: datetime | None) -> str:
    return timezone.localtime(moment).strftime("%d.%m.%Y %H:%M") if moment else ""
