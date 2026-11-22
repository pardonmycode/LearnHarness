"""Group overview and its CSV export."""

from __future__ import annotations

import csv

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.text import slugify

from ..models import LearningGroup, SkillLevel
from .common import ALL, UNGROUPED, _csv_response, _local, _select, build_table


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
