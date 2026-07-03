"""
apps/backoffice/dashboards.py
=============================
Aggregation helpers for the backoffice dashboard (KPIs and analytics).

These functions are pure read queries returning plain dicts/lists so the
views stay thin and the numbers can be tested in isolation.
"""

from datetime import timedelta

from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.b2b.models import B2BRequest
from apps.backoffice.selectors import count_pending_b2b_accounts
from apps.checkout.models import Order, OrderItem
from apps.checkout.selectors import PAID_STATUSES, channel_revenue
from apps.shop.models import Stock


def get_kpis():
    """Return headline KPIs for the dashboard."""
    paid_orders = Order.objects.filter(status__in=PAID_STATUSES)

    revenue = paid_orders.aggregate(total=Sum("total_amount"))["total"] or 0
    order_count = paid_orders.count()
    avg_basket = (revenue / order_count) if order_count else 0

    return {
        "revenue": revenue,
        "order_count": order_count,
        "avg_basket": round(avg_basket, 2),
        "pending_orders": Order.objects.filter(status="pending").count(),
        # Stock.is_low is a @property, so no parentheses.
        "low_stock_count": sum(1 for s in Stock.objects.all() if s.is_low),
        "new_b2b_count": B2BRequest.objects.filter(status="new").count(),
        # --- B2B KPIs (feed the pro-validation workflow + cockpit parity) ---
        # Both read canonical sources shared with the cockpit: B2BAccount.status
        # (via the backoffice selector) and Order.channel="b2b" (via
        # checkout.selectors.channel_revenue) -> the two dashboards can't diverge.
        "pending_b2b_accounts": count_pending_b2b_accounts(),
        "b2b_revenue": channel_revenue("b2b"),
    }


def get_revenue_last_30_days():
    """Return daily revenue for the last 30 days (for a chart)."""
    since = timezone.now() - timedelta(days=30)
    orders = (
        Order.objects.filter(status__in=PAID_STATUSES, created_at__gte=since)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Sum("total_amount"))
        .order_by("day")
    )
    return list(orders)


def get_top_products(limit=5):
    """Return the best-selling products by quantity."""
    return list(
        OrderItem.objects.values("sku__product__name_fr")
        .annotate(qty=Sum("quantity"))
        .order_by("-qty")[:limit]
    )


def get_low_stock_items():
    """Return stock rows at or below their alert threshold."""
    # Stock.is_low is a @property, so no parentheses.
    return [s for s in Stock.objects.select_related("sku") if s.is_low]
