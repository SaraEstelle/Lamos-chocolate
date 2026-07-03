"""
apps/analytics/selectors.py
===========================
Read helpers that turn raw events into KPI numbers (used later by the cockpit).
"""

from datetime import timedelta

from django.db.models import Count, Sum
from django.utils import timezone

from apps.analytics.models import Event


def revenue_by_canton(days=30):
    """Total purchase value grouped by canton over the period."""
    since = timezone.now() - timedelta(days=days)
    return list(
        Event.objects.filter(event_type="purchase", created_at__gte=since)
        .values("canton")
        .annotate(total=Sum("value_chf"))
        .order_by("-total")
    )


def conversion_rate(days=30):
    """purchase / product_view as a simple funnel proxy over the period."""
    since = timezone.now() - timedelta(days=days)
    qs = Event.objects.filter(created_at__gte=since)
    views = qs.filter(event_type="product_view").count()
    purchases = qs.filter(event_type="purchase").count()
    return round(purchases / views, 4) if views else 0.0


def channel_split(days=30):
    """Revenue split by channel (b2c vs b2b) for the donut chart."""
    since = timezone.now() - timedelta(days=days)
    return list(
        Event.objects.filter(event_type="purchase", created_at__gte=since)
        .values("channel")
        .annotate(total=Sum("value_chf"), count=Count("id"))
    )
