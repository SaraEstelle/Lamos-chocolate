"""
apps/cockpit/views.py
=====================
Executive cockpit (PRD §8): a read-only decision dashboard, standalone from
the public site and distinct from the OPS backoffice.

Access is restricted to staff for now. PRD §8.4 calls for a dedicated
read-only 'executive' role; until that role exists, staff access is the gate.
"""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.cockpit import selectors
from apps.cockpit.models import CantonTarget, CockpitObjective, ProductTarget
from apps.common.constants import SwissCantonChoices


@staff_member_required
@require_http_methods(["GET"])
def cockpit_view(request):
    """Executive home: Pulse band + channel split + top SKUs + revenue trend."""
    context = {
        "active": "home",
        "pulse": selectors.get_pulse(),
        "channel_split": selectors.get_channel_split(),
        "top_skus": selectors.get_top_skus(),
        "revenue_trend": selectors.get_revenue_trend(),
    }
    return render(request, "cockpit/dashboard.html", context)


@staff_member_required
@require_http_methods(["GET"])
def heatmap_view(request):
    """Sales heatmap: realised revenue broken down by Swiss canton."""
    context = {
        "active": "heatmap",
        "canton": selectors.get_canton_revenue(),
    }
    return render(request, "cockpit/heatmap.html", context)


@staff_member_required
@require_http_methods(["GET"])
def products_view(request):
    """Product study overview: per-product KPIs (revenue, units, gross margin)."""
    context = {
        "active": "products",
        "products": selectors.get_product_overview(),
    }
    return render(request, "cockpit/products.html", context)


@staff_member_required
@require_http_methods(["GET"])
def inventory_view(request):
    """Inventory runway + production relaunch alerts (US-22 KPIs 5 & 6)."""
    context = {
        "active": "inventory",
        "inventory": selectors.get_inventory_forecast(),
    }
    return render(request, "cockpit/inventory.html", context)


@staff_member_required
@require_http_methods(["GET"])
def etude_view(request):
    """Behavioural study: orders by weekday + acquisition funnel."""
    context = {
        "active": "etude",
        "weekday": selectors.get_orders_by_weekday(),
        "hourly": selectors.get_orders_by_hour(),
        "funnel": selectors.get_funnel(),
        "top_viewed": selectors.get_top_viewed(),
        "top_ordered": selectors.get_top_ordered(),
    }
    return render(request, "cockpit/etude.html", context)


def _parse_int(raw, default=0, minimum=0):
    """Best-effort positive-int parse from a form field, clamped at minimum."""
    try:
        return max(int(raw), minimum)
    except (TypeError, ValueError):
        return default


@staff_member_required
@require_http_methods(["GET", "POST"])
def pilotage_view(request):
    """Interactive objectives: set company targets + per-product unit goals.

    GET renders the form pre-filled with current values; POST persists the
    objectives then redirects (Post-Redirect-Get) to avoid resubmission.
    """
    if request.method == "POST":
        obj = CockpitObjective.load()
        obj.daily_revenue_chf = _parse_int(
            request.POST.get("daily_revenue_chf"), obj.daily_revenue_chf)
        obj.monthly_revenue_chf = _parse_int(
            request.POST.get("monthly_revenue_chf"), obj.monthly_revenue_chf)
        obj.monthly_capacity_units = _parse_int(
            request.POST.get("monthly_capacity_units"), obj.monthly_capacity_units)
        try:
            obj.target_margin_pct = max(
                min(float(request.POST.get("target_margin_pct")), 100), 0)
        except (TypeError, ValueError):
            pass
        obj.updated_by = request.user
        obj.save()

        # Per-product monthly unit objectives (fields named target_<product_id>).
        for key, value in request.POST.items():
            if not key.startswith("target_"):
                continue
            suffix = key[len("target_"):]
            if not suffix.isdigit():
                continue
            ProductTarget.objects.update_or_create(
                product_id=int(suffix),
                defaults={"monthly_units": _parse_int(value, 0)},
            )

        # Per-canton revenue objectives (fields named canton_<CODE>).
        valid_cantons = set(SwissCantonChoices.values)
        for key, value in request.POST.items():
            if not key.startswith("canton_"):
                continue
            code = key[len("canton_"):]
            if code not in valid_cantons:
                continue
            CantonTarget.objects.update_or_create(
                canton=code,
                defaults={"monthly_revenue_chf": _parse_int(value, 0)},
            )

        messages.success(request, "Objectifs enregistrés.")
        return redirect(reverse("cockpit:pilotage"))

    context = {
        "active": "pilotage",
        "pilotage": selectors.get_pilotage(),
    }
    return render(request, "cockpit/pilotage.html", context)


@staff_member_required
@require_http_methods(["GET"])
def product_detail_view(request, product_id):
    """Drill-down study for a single product."""
    detail = selectors.get_product_detail(product_id)
    if detail is None:
        raise Http404("Product not found")
    context = {
        "active": "products",
        "detail": detail,
    }
    return render(request, "cockpit/product_detail.html", context)
