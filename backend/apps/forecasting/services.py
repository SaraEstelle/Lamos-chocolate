"""
apps/forecasting/services.py
============================
Read helpers that surface forecasting data for the UI.

The heavy calculation logic lives in the models/calculations; here we just
assemble what the templates need.
"""

from apps.shop.models import SKU, Stock
from apps.shop.services import get_delivery_estimates


def get_production_estimates():
    """
    For every active SKU, return its delivery estimates per zone.

    Returns a list of dicts: {"sku": SKU, "estimates": [{zone, days}, ...]}.
    """
    result = []
    for sku in SKU.objects.filter(is_active=True).select_related("product"):
        result.append(
            {
                "sku": sku,
                "estimates": get_delivery_estimates(sku, quantity=1),
            }
        )
    return result


def get_stockout_risks():
    """
    Return SKUs at risk of stockout (stock at or below threshold).

    Returns a list of dicts: {"sku": SKU, "quantity": int, "threshold": int}.
    """
    risks = []
    for stock in Stock.objects.select_related("sku__product"):
        # Stock.is_low is a @property, so no parentheses.
        if stock.is_low:
            risks.append(
                {
                    "sku": stock.sku,
                    "quantity": stock.quantity,
                    "threshold": stock.threshold_alert,
                }
            )
    return risks
