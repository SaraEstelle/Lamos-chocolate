"""
apps/checkout/selectors.py
==========================
Read-only queries over the Order domain.

This module is the single source of truth for "what counts as realised
revenue" and how it splits by sales channel. Both the staff backoffice
dashboard and the executive cockpit read from here so the two never disagree
(before this, PAID_STATUSES and the channel split were duplicated in
apps/backoffice/dashboards.py and apps/cockpit/selectors.py).
"""

from datetime import timedelta

from django.db.models import Count, Sum
from django.utils import timezone

from apps.checkout.models import Order

# Statuses that count as realised (paid) revenue. Canonical definition:
# import this instead of re-declaring the list per app.
PAID_STATUSES = ("paid", "processing", "shipped", "delivered")


def paid_orders():
    """Base queryset of orders that count as realised revenue."""
    return Order.objects.filter(status__in=PAID_STATUSES)


def revenue_by_channel(days=None):
    """
    Realised revenue + order count per sales channel (b2c / b2b).

    Returns a list of dicts: [{"channel": "b2b", "revenue": ..., "orders": ...}].
    Pass ``days`` to restrict to a trailing window; omit it for all-time.
    """
    qs = paid_orders()
    if days:
        qs = qs.filter(created_at__gte=timezone.now() - timedelta(days=days))
    return list(
        qs.values("channel")
        .annotate(revenue=Sum("total_amount"), orders=Count("id"))
        .order_by("-revenue")
    )


def channel_revenue(channel, days=None):
    """
    Total realised revenue for a single channel (e.g. "b2b"), as a scalar.

    Convenience wrapper for a dashboard KPI card. Returns 0 when the channel
    has no paid orders in the window.
    """
    qs = paid_orders().filter(channel=channel)
    if days:
        qs = qs.filter(created_at__gte=timezone.now() - timedelta(days=days))
    return qs.aggregate(total=Sum("total_amount"))["total"] or 0
