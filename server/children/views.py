"""Teacher overview: one table per group with the level of every skill per child."""

from __future__ import annotations

from dataclasses import dataclass

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Prefetch
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Child, LearningGroup, SkillLevel, SkillProgress

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


@staff_member_required
def overview(request: HttpRequest, selection: str = ALL) -> HttpResponse:
    chosen = request.GET.get("gruppe")
    if chosen is not None:
        # The group selector submits ?gruppe=…; turn it into a clean, bookmarkable URL.
        if chosen.isdigit() or chosen == UNGROUPED:
            return redirect("overview-group", selection=chosen)
        return redirect("overview")

    children = Child.objects.filter(active=True).prefetch_related(
        Prefetch(
            "skills", queryset=SkillProgress.objects.only("child_id", "skill_id", "label", "level")
        )
    )
    group = None
    if selection == UNGROUPED:
        children = children.filter(group__isnull=True)
        title = "Übersicht: ohne Gruppe"
    elif selection != ALL:
        if not selection.isdigit():
            return redirect("overview")
        group = get_object_or_404(LearningGroup, pk=int(selection))
        children = children.filter(group=group)
        title = f"Übersicht: {group.name}"
    else:
        children = children.select_related("group")
        title = "Übersicht: alle Gruppen"

    columns, rows = build_table(list(children.order_by("pseudonym")))
    context = {
        **admin.site.each_context(request),
        "title": title,
        "groups": LearningGroup.objects.all(),
        "selection": selection,
        "selected_group": group,
        "all_value": ALL,
        "ungrouped_value": UNGROUPED,
        "show_group": selection == ALL,
        "columns": columns,
        "rows": rows,
        "levels": SkillLevel.choices,
    }
    return render(request, "children/overview.html", context)
