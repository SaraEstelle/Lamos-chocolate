"""
apps/shop/services.py
=====================
Catalog business logic.

Limited to the delivery-time estimation shown on the product page — the
catalog itself is read-only (browsing and searching).
"""

from apps.shop.models import SKU, ShippingZone


def get_delivery_estimates(sku: SKU, quantity: int = 1) -> list[dict]:
    """Return the estimated delivery time per shipping zone for a SKU.

    Args:
        sku: The SKU to estimate delivery for.
        quantity: Ordered quantity used by the forecasting model.

    Returns:
        A list of ``{"zone": ShippingZone, "days": int}`` computed with
        ``SKU.calculate_estimated_days`` for every configured zone. No customer
        country is stored, so an estimate is surfaced for each zone instead of
        a single personalised one (design "Approach A").
    """
    return [
        {"zone": zone, "days": sku.calculate_estimated_days(quantity, zone)}
        for zone in ShippingZone.objects.all()
    ]
