"""Stripe webhook endpoint.

Stripe calls this server-to-server, so there is no Django session: the order is
rebuilt entirely from the session metadata set in ``stripe.py``. The signature
is verified against ``STRIPE_WEBHOOK_SECRET`` before anything is trusted, and
order creation is idempotent so Stripe's retries never duplicate an order.
"""

import json
import logging

import stripe
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.accounts.models import Customer
from apps.common.constants import ChannelChoices, CurrencyChoices, LanguageChoices
from apps.shop.models import SKU

from .services import create_paid_order, send_order_confirmation

logger = logging.getLogger(__name__)

SHIP_PREFIX = "ship_"


@csrf_exempt
@require_POST
def stripe_webhook_view(request):
    """Verify the Stripe signature and fulfill completed checkout sessions."""
    try:
        event = stripe.Webhook.construct_event(
            request.body,
            request.META.get("HTTP_STRIPE_SIGNATURE", ""),
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        logger.warning("Rejected Stripe webhook: invalid payload or signature")
        return HttpResponseBadRequest("Invalid payload or signature")

    if event["type"] == "checkout.session.completed":
        _fulfill_checkout(event["data"]["object"])

    return HttpResponse(status=200)


def _fulfill_checkout(session):
    """Create the paid order from a completed session's metadata."""
    metadata = session.get("metadata") or {}

    customer = Customer.objects.filter(id=metadata.get("customer_id")).first()
    if customer is None:
        logger.error(
            "Webhook session %s references unknown customer_id %r",
            session.get("id"),
            metadata.get("customer_id"),
        )
        return

    items = _resolve_items(metadata.get("cart", "{}"))
    if not items:
        logger.error("Webhook session %s has no resolvable items", session.get("id"))
        return

    shipping = {
        key[len(SHIP_PREFIX) :]: value
        for key, value in metadata.items()
        if key.startswith(SHIP_PREFIX)
    }

    order, created = create_paid_order(
        customer=customer,
        items=items,
        shipping=shipping,
        currency=metadata.get("currency", CurrencyChoices.EUR),
        language=metadata.get("language", LanguageChoices.FR),
        channel=metadata.get("channel", ChannelChoices.B2C),
        stripe_session_id=session.get("id"),
        stripe_payment_intent=session.get("payment_intent") or "",
    )

    if created:
        # create_paid_order's transaction has already committed by now, so the
        # confirmation email is sent against a persisted order.
        send_order_confirmation(order)


def _resolve_items(cart_json):
    """Turn the ``{sku_id: quantity}`` metadata map into ``(sku, qty)`` pairs."""
    try:
        cart_map = json.loads(cart_json)
    except (TypeError, ValueError):
        return []

    skus_by_id = {
        str(sku.id): sku
        for sku in SKU.objects.filter(id__in=[int(i) for i in cart_map])
    }
    return [
        (skus_by_id[sku_id], quantity)
        for sku_id, quantity in cart_map.items()
        if sku_id in skus_by_id
    ]
