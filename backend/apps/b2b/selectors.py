"""
apps/b2b/selectors.py
=====================
Read-only queries for the B2B app (never write).
"""

from datetime import timedelta
from django.utils import timezone
from apps.b2b.models import B2BRequest
from apps.b2b.models import B2BProductInfo
from apps.checkout.models import Order
from django.db.models import Count, Sum

def has_recent_duplicate(*, contact_email, company_name, within_minutes=10):
    """Return True if an identical request was just submitted (double-submit guard)."""
    since = timezone.now() - timedelta(minutes=within_minutes)
    return (
        B2BRequest.objects.filter(
            contact_email__iexact=contact_email,
            company_name__iexact=company_name,
            created_at__gte=since,
        ).exists()
    )

def get_pro_catalogue():
    """
    Active B2B SKUs with their stock and B2B info, for the pro catalogue.

    select_related pulls the SKU, its product and its stock in one query
    (no N+1). `sku__stock` is the reverse OneToOne (Stock.related_name="stock").
    """
    return (
        B2BProductInfo.objects
        .filter(is_b2b_available=True, sku__is_active=True)
        .select_related("sku", "sku__product", "sku__stock")
        .order_by("sku__product__name_fr", "sku__weight_g")
    )


def get_b2b_orders(account, limit=20):
    """
    Past B2B orders for this account's customer (channel="b2b").

    Order.channel is added by F-DATA. We scope strictly to the account owner so a
    pro can never see another account's orders.
    """
    return (
        Order.objects
        .filter(customer=account.customer, channel="b2b")
        .prefetch_related("items__sku")
        .order_by("-created_at")[:limit]
    )

# Statuses that mean "the order is still moving" (not delivered/cancelled).
IN_PROGRESS_ORDER_STATUSES = ("pending", "paid", "processing", "shipped")


def get_b2b_orders_in_progress(account, limit=20):
    """B2B orders that are not yet delivered/cancelled (the 'en cours' tab)."""
    return (
        Order.objects
        .filter(customer=account.customer, channel="b2b",
                status__in=IN_PROGRESS_ORDER_STATUSES)
        .prefetch_related("items__sku__product")
        .order_by("-created_at")[:limit]
    )


def get_exclusive_products():
    """
    Pro-only 'exclusive / pre-order' rows: B2B SKUs flagged NEW or COMING_SOON.
    Feeds the 'Produits exclusifs' tab. Read-only, no N+1 (select_related).
    """
    return (
        B2BProductInfo.objects
        .filter(is_b2b_available=True, sku__is_active=True,
                availability_status__in=("new", "coming_soon"))
        .select_related("sku", "sku__product")
        .order_by("availability_status", "sku__product__name_fr")
    )


def get_b2b_dashboard_kpis(account):
    """
    Small header KPIs for the pro dashboard (all read-only, one query each).

    Returns a plain dict the template can read directly:
      - orders_in_progress : how many orders are still moving
      - orders_total       : total B2B orders ever
      - revenue_total      : sum of total_amount over delivered orders (CHF)
    """
    base = Order.objects.filter(customer=account.customer, channel="b2b")
    agg = base.aggregate(
        orders_total=Count("id"),
        revenue_total=Sum("total_amount"),
    )
    return {
        "orders_in_progress": base.filter(
            status__in=IN_PROGRESS_ORDER_STATUSES
        ).count(),
        "orders_total": agg["orders_total"] or 0,
        "revenue_total": agg["revenue_total"] or 0,
    }