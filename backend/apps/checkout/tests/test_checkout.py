"""Unit tests for checkout models: Order and OrderItem.

Also covers the two database integrity rules added to match the spec:
- Order.shipping_zone foreign key (delivery zone at order time)
- order_items.quantity > 0 CHECK constraint
"""

import re
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction


def _make_order(customer, shipping_zone=None):
    from apps.checkout.models import Order

    return Order.objects.create(
        customer=customer,
        order_number=Order.generate_order_number(),
        total_amount="25.80",
        shipping_zone=shipping_zone,
    )


class TestOrderNumber:
    def test_order_number_format(self):
        from apps.checkout.models import Order

        order_number = Order.generate_order_number()
        assert re.match(r"^LM-\d{8}-[A-Z0-9]{5}$", order_number)

    def test_order_number_uniqueness(self):
        from apps.checkout.models import Order

        numbers = {Order.generate_order_number() for _ in range(100)}
        assert len(numbers) == 100


class TestOrderShippingZone:
    """Écart 1 — shipping_zone is a real FK on orders."""

    def test_order_keeps_shipping_zone(self, db, sample_customer, sample_shipping_zone):
        order = _make_order(sample_customer, shipping_zone=sample_shipping_zone)
        order.refresh_from_db()
        assert order.shipping_zone == sample_shipping_zone
        assert order.shipping_zone.delay_days == 2

    def test_shipping_zone_reverse_relation(
        self, db, sample_customer, sample_shipping_zone
    ):
        _make_order(sample_customer, shipping_zone=sample_shipping_zone)
        assert sample_shipping_zone.orders.count() == 1

    def test_shipping_zone_is_optional(self, db, sample_customer):
        order = _make_order(sample_customer, shipping_zone=None)
        order.refresh_from_db()
        assert order.shipping_zone is None


class TestOrderItem:
    def test_subtotal_is_computed_on_save(self, db, sample_customer, sample_product):
        from apps.checkout.models import OrderItem

        _, sku, _ = sample_product
        order = _make_order(sample_customer)
        item = OrderItem.objects.create(
            order=order, sku=sku, quantity=3, unit_price=Decimal("12.90")
        )
        # subtotal = quantity * unit_price = 3 * 12.90
        assert item.subtotal == Decimal("38.70")

    def test_quantity_zero_is_rejected(self, db, sample_customer, sample_product):
        """Écart 2 — CHECK (quantity > 0); PositiveIntegerField alone allows 0."""
        from apps.checkout.models import OrderItem

        _, sku, _ = sample_product
        order = _make_order(sample_customer)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                OrderItem.objects.create(
                    order=order, sku=sku, quantity=0, unit_price=Decimal("12.90")
                )


class TestPayment:
    def test_payment_defaults(self, db, sample_customer):
        from apps.checkout.models import Payment

        order = _make_order(sample_customer)
        payment = Payment.objects.create(
            order=order, stripe_payment_intent="pi_test_123", amount=Decimal("25.80")
        )
        assert payment.status == "pending"
        assert payment.currency == "EUR"
        assert payment.paid_at is None

    def test_payment_one_to_one_reverse(self, db, sample_customer):
        from apps.checkout.models import Payment

        order = _make_order(sample_customer)
        payment = Payment.objects.create(
            order=order, stripe_payment_intent="pi_test_456", amount=Decimal("10.00")
        )
        assert order.payment == payment

    def test_stripe_payment_intent_is_unique(self, db, sample_customer):
        from apps.checkout.models import Payment

        Payment.objects.create(
            order=_make_order(sample_customer),
            stripe_payment_intent="pi_duplicate",
            amount=Decimal("5.00"),
        )
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Payment.objects.create(
                    order=_make_order(sample_customer),
                    stripe_payment_intent="pi_duplicate",
                    amount=Decimal("5.00"),
                )
