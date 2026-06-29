"""
apps/checkout/services.py
=========================
Checkout domain logic: creating a paid order from a confirmed Stripe payment
(stock decrement, snapshots, idempotency) plus the transactional emails that
accompany the checkout flow.
"""

import logging
from decimal import Decimal

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from apps.checkout.models import Order, OrderItem, Payment
from apps.common.constants import (
    ChannelChoices,
    CurrencyChoices,
    LanguageChoices,
    OrderStatusChoices,
    PaymentStatusChoices,
)
from apps.shop.models import Stock

logger = logging.getLogger(__name__)


def create_paid_order(
    *,
    customer,
    items,
    shipping=None,
    currency=CurrencyChoices.EUR,
    language=LanguageChoices.FR,
    stripe_session_id,
    stripe_payment_intent="",
    total_amount=None,
    channel=ChannelChoices.B2C,
):
    """Create a paid order with its items and payment, decrementing stock.

    Designed to be called once a Stripe payment is confirmed. The whole write
    happens in a single transaction with per-SKU row locks, so concurrent
    orders cannot oversell.

    Idempotent on ``stripe_session_id``: if an order already exists for that
    Stripe session (e.g. a redelivered webhook), it is returned untouched.

    Args:
        customer: the buying ``accounts.Customer``.
        items: iterable of ``(sku, quantity)`` pairs; the unit price is
            snapshotted from ``sku.price`` at creation time.
        shipping: optional dict of shipping fields without the ``shipping_``
            prefix (``first_name``, ``last_name``, ``address1``, ``address2``,
            ``city``, ``postal_code``, ``country``).
        total_amount: authoritative total; computed from the items when ``None``.

    Returns:
        ``(order, created)`` where ``created`` is ``False`` on idempotent hits.

    Raises:
        ValueError: if a SKU has insufficient stock (the transaction is rolled
            back, so no partial order is left behind).
    """
    if stripe_session_id:
        existing = Order.objects.filter(stripe_session_id=stripe_session_id).first()
        if existing is not None:
            return existing, False

    lines = [(sku, int(quantity)) for sku, quantity in items]
    shipping_fields = {f"shipping_{k}": v for k, v in (shipping or {}).items()}

    with transaction.atomic():
        order = Order.objects.create(
            customer=customer,
            order_number=Order.generate_order_number(),
            status=OrderStatusChoices.PAID,
            total_amount=total_amount if total_amount is not None else Decimal("0"),
            currency=currency,
            language=language,
            channel=channel,
            stripe_session_id=stripe_session_id,
            **shipping_fields,
        )

        computed_total = Decimal("0")
        order_items = []
        for sku, quantity in lines:
            stock = Stock.objects.select_for_update().get(sku=sku)
            stock.decrement(quantity)  # raises ValueError if insufficient
            unit_price = Decimal(sku.price)
            subtotal = unit_price * quantity
            computed_total += subtotal
            order_items.append(
                OrderItem(
                    order=order,
                    sku=sku,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                )
            )
        OrderItem.objects.bulk_create(order_items)

        if total_amount is None:
            order.total_amount = computed_total
            order.save(update_fields=["total_amount"])

        Payment.objects.create(
            order=order,
            stripe_payment_intent=stripe_payment_intent or order.order_number,
            amount=order.total_amount,
            currency=currency,
            status=PaymentStatusChoices.SUCCEEDED,
            paid_at=timezone.now(),
        )

    return order, True


def _send_html_email(subject, to_email, template, context):
    """Render an HTML template and send it (with a plain-text fallback)."""
    try:
        html_body = render_to_string(template, context)
        msg = EmailMultiAlternatives(
            subject=subject,
            body="Please view this email in an HTML-capable client.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        return True
    except Exception:  # noqa: BLE001 - never break the flow on email error
        logger.exception("Failed to send email:%s", template)
        return False


def send_order_confirmation(order):
    """Send the order confirmation email to the customer."""
    return _send_html_email(
        subject="Order confirmation — Lamos Chocolate",
        to_email=order.customer.email,
        template="emails/order_confirmation.html",
        context={"order": order},
    )


def send_order_shipped(order):
    """Send the shipping notification email to the customer."""
    return _send_html_email(
        subject="Your order has shipped — Lamos Chocolate",
        to_email=order.customer.email,
        template="emails/order_shipped.html",
        context={"order": order},
    )