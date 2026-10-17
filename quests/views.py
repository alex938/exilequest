import json
from functools import lru_cache
from pathlib import Path

from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from django_ratelimit.decorators import ratelimit

from .models import Quest

ACTS = range(1, 11)


@lru_cache(maxsize=1)
def _get_dataset_info():
    """Read dataset metadata from quests.json (cached for the process lifetime)."""
    filepath = Path(__file__).resolve().parent / "data" / "quests.json"
    try:
        with open(filepath) as f:
            data = json.load(f)
        return {
            "version": data.get("dataset_version", "unknown"),
            "last_verified_at": data.get("last_verified_at", "unknown"),
            "sources": data.get("sources", []),
            "notes": data.get("notes", ""),
        }
    except Exception:
        return {"version": "unknown", "last_verified_at": "unknown", "sources": [], "notes": ""}


def _get_totals():
    """Summary stats over the full dataset, in a single query."""
    return Quest.objects.aggregate(
        total_quests=Count("id"),
        total_passive=Sum("passive_points", filter=Q(gives_passive_point=True), default=0),
        total_refund=Sum("refund_points", filter=Q(gives_refund_points=True), default=0),
    )


@require_GET
@ratelimit(key="ip", rate="60/m", block=True)
@cache_control(public=True, max_age=300)
def quest_list(request):
    """Public quest reference page — shows all quests grouped by act."""
    quests = Quest.objects.all()

    # Apply filters
    filter_act = request.GET.get("act", "")
    filter_reward = request.GET.get("reward", "")
    search_q = request.GET.get("q", "").strip()[:200]  # Cap search length

    if filter_act:
        try:
            quests = quests.filter(act=int(filter_act))
        except (ValueError, TypeError):
            filter_act = ""

    if filter_reward == "passive":
        quests = quests.filter(gives_passive_point=True)
    elif filter_reward == "refund":
        quests = quests.filter(gives_refund_points=True)
    elif filter_reward == "other":
        quests = quests.filter(gives_other=True)
    elif filter_reward == "required":
        quests = quests.filter(is_required=True)

    if search_q:
        quests = quests.filter(
            Q(name__icontains=search_q)
            | Q(npc__icontains=search_q)
            | Q(primary_zone__icontains=search_q)
            | Q(hint_text__icontains=search_q)
            | Q(other_reward_text__icontains=search_q)
        )

    # Group by act
    acts = {}
    for quest in quests:
        acts.setdefault(quest.act, []).append(quest)

    return render(request, "quests/quest_list.html", {
        "acts": acts,
        "act_choices": ACTS,
        "filter_act": filter_act,
        "filter_reward": filter_reward,
        "search_q": search_q,
        "is_filtered": bool(filter_act or filter_reward or search_q),
        **_get_totals(),
        "dataset_info": _get_dataset_info(),
    })


@require_GET
def healthz(request):
    """Lightweight health-check endpoint for Docker / load balancers."""
    return JsonResponse({"status": "ok"})
