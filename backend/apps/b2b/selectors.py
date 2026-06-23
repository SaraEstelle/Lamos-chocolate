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