"""
apps/analytics/services.py
==========================
Helpers to record events from anywhere, without ever breaking the calling flow.
"""

import logging

from apps.analytics.models import Event
from apps.common.consent import analytics_allowed

logger = logging.getLogger(__name__)


def track_event(
    event_type,
    *,
    customer=None,
    channel="",
    canton="",
    campaign_period="",
    value_chf=None,
    **properties,
):
    """
    Record a single event. NEVER raises to the caller.

    Usage:
        track_event("add_to_cart", customer=request.user, channel="b2c",
                    sku="KUNAFA-80", quantity=2, value_chf="23.80")
    """
    try:
        return Event.objects.create(
            event_type=event_type,
            customer=customer if getattr(customer, "is_authenticated", False) else None,
            channel=channel or "",
            canton=canton or "",
            campaign_period=campaign_period or "",
            value_chf=value_chf,
            properties=properties or {},
        )
    except Exception:  # noqa: BLE001 - tracking must never break the user flow
        logger.exception("Failed to record event%s", event_type)
        return None


def track_purchase(order):
    """Convenience wrapper to record a purchase from an Order instance."""
    customer = getattr(order, "customer", None)
    canton = getattr(customer, "canton", "") if customer else ""
    lines = [
        {"sku": item.sku.sku_code, "qty": item.quantity, "price": str(item.unit_price)}
        for item in order.items.all()
    ]
    return track_event(
        "purchase",
        customer=customer,
        channel=getattr(order, "channel", "b2c"),
        canton=canton,
        campaign_period=getattr(order, "campaign_period", ""),
        value_chf=order.total_amount,
        order_id=order.order_number,
        lines=lines,
    )


def track_event_if_consented(request, event_type, **kwargs):
    """Track only if the visitor accepted analytics cookies."""
    if analytics_allowed(request):
        return track_event(event_type, **kwargs)
    return None
