"""
apps/cockpit/admin.py
=====================
Fallback editing for the cockpit objectives. The primary editing surface is
the Pilotage tab; the admin is a safety net for staff.
"""

from django.contrib import admin

from .models import CantonTarget, CockpitObjective, ProductTarget


@admin.register(CockpitObjective)
class CockpitObjectiveAdmin(admin.ModelAdmin):
    list_display = (
        "__str__", "daily_revenue_chf", "monthly_revenue_chf",
        "monthly_capacity_units", "target_margin_pct", "updated_at",
    )


@admin.register(ProductTarget)
class ProductTargetAdmin(admin.ModelAdmin):
    list_display = ("product", "monthly_units", "updated_at")
    autocomplete_fields = ("product",)


@admin.register(CantonTarget)
class CantonTargetAdmin(admin.ModelAdmin):
    list_display = ("canton", "monthly_revenue_chf", "updated_at")
