import json
from collections import OrderedDict
from pathlib import Path

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET
from django_ratelimit.decorators import ratelimit

from .models import Quest


def _get_dataset_info():
    """Read dataset metadata from quests.json."""
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


@require_GET
@ratelimit(key="ip", rate="60/m", block=True)
@cache_control(public=True, max_age=300)
def quest_list(request):
    """Public quest reference page — shows all quests grouped by act."""
    quests = Quest.objects.all()

    # Apply filters
    filter_act = request.GET.get("act")
    filter_reward = request.GET.get("reward")
    search_q = request.GET.get("q")

    if filter_act:
        try:
            quests = quests.filter(act=int(filter_act))
        except (ValueError, TypeError):
            pass

    if filter_reward == "passive":
        quests = quests.filter(gives_passive_point=True)
    elif filter_reward == "refund":
        quests = quests.filter(gives_refund_points=True)
    elif filter_reward == "other":
        quests = quests.filter(gives_other=True)

    if search_q:
        sq = search_q.strip()[:200]  # Cap search length
        from django.db.models import Q
        quests = quests.filter(
            Q(name__icontains=sq)
            | Q(npc__icontains=sq)
            | Q(primary_zone__icontains=sq)
            | Q(hint_text__icontains=sq)
        )

    # Group by act
    acts = OrderedDict()
    for quest in quests:
        acts.setdefault(quest.act, []).append(quest)

    # Summary stats (always from full dataset)
    all_quests = Quest.objects.all()
    total_passive = sum(q.passive_points for q in all_quests if q.gives_passive_point)
    total_refund = sum(q.refund_points for q in all_quests if q.gives_refund_points)
    total_quests = all_quests.count()

    return render(request, "quests/quest_list.html", {
        "acts": dict(acts),
        "filter_act": filter_act or "",
        "filter_reward": filter_reward or "",
        "search_q": search_q or "",
        "total_passive": total_passive,
        "total_refund": total_refund,
        "total_quests": total_quests,
        "dataset_info": _get_dataset_info(),
    })


@require_GET
def healthz(request):
    """Lightweight health-check endpoint for Docker / load balancers."""
    return JsonResponse({"status": "ok"})
