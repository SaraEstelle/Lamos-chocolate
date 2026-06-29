"""Stripe Checkout session building.

The order is created only once the webhook confirms payment. That webhook runs
server-to-server with no Django session, so everything it needs to rebuild the
order (cart lines, shipping, customer, currency) travels inside the Stripe
session ``metadata`` and is read back in ``webhooks.py``.
"""

import json
from decimal import ROUND_HALF_UP, Decimal

import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def _to_minor_units(amount) -> int:
    """Convert a decimal price to Stripe's smallest currency unit (cents)."""
    return int((Decimal(amount) * 100).to_integral_value(rounding=ROUND_HALF_UP))


def build_line_items(cart_items):
    """Map cart lines to Stripe ``line_items`` with inline price data."""
    line_items = []
    for item in cart_items:
        line_items.append(
            {
                "price_data": {
                    "currency": item.sku.currency.lower(),
                    "product_data": {"name": item.display_name},
                    "unit_amount": _to_minor_units(item.sku.price),
                },
                "quantity": item.quantity,
            }
        )
    return line_items


def build_metadata(*, customer, cart_items, shipping, currency, language, channel):
    """Encode everything the webhook needs to rebuild the order.

    The cart is stored as a compact ``{sku_id: quantity}`` JSON map; shipping
    fields are flattened with a ``ship_`` prefix. Stripe caps each metadata
    value at 500 characters, which is ample for a typical basket.
    """
    cart_map = {str(item.sku.id): item.quantity for item in cart_items}
    metadata = {
        "customer_id": str(customer.id),
        "cart": json.dumps(cart_map, separators=(",", ":")),
        "currency": currency,
        "language": language,
        "channel": channel,
    }
    for key, value in (shipping or {}).items():
        metadata[f"ship_{key}"] = value or ""
    return metadata


def create_checkout_session(
    *,
    customer,
    cart_items,
    shipping,
    currency,
    language,
    channel,
    success_url,
    cancel_url,
):
    """Create a Stripe Checkout session and return it (with ``.url``/``.id``)."""
    return stripe.checkout.Session.create(
        mode="payment",
        line_items=build_line_items(cart_items),
        customer_email=customer.email,
        metadata=build_metadata(
            customer=customer,
            cart_items=cart_items,
            shipping=shipping,
            currency=currency,
            language=language,
            channel=channel,
        ),
        success_url=success_url,
        cancel_url=cancel_url,
    )
