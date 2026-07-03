"""Unit tests for the checkout order-creation service (``create_paid_order``).

Covers the Stripe-independent domain logic: building a paid Order with its
items and Payment, snapshotting prices, decrementing stock atomically, and
staying idempotent against duplicate webhook deliveries (same session id).
"""

from decimal import Decimal

import pytest

from apps.checkout.services import create_paid_order

SHIPPING = {
    "first_name": "Marie",
    "last_name": "Test",
    "address1": "Rue du Test 1",
    "city": "Genève",
    "postal_code": "1200",
    "country": "CH",
}


@pytest.mark.payment
class TestCreatePaidOrder:
    def test_creates_paid_order(self, db, sample_customer, sample_product):
        _, sku, _ = sample_product
        order, created = create_paid_order(
            customer=sample_customer,
            items=[(sku, 2)],
            shipping=SHIPPING,
            currency="EUR",
            language="fr",
            stripe_session_id="cs_test_1",
            stripe_payment_intent="pi_test_1",
        )
        assert created is True
        assert order.status == "paid"
        assert order.order_number.startswith("LM-")
        assert order.customer == sample_customer
        assert order.currency == "EUR"
        assert order.stripe_session_id == "cs_test_1"

    def test_creates_items_with_price_snapshot(
        self, db, sample_customer, sample_product
    ):
        _, sku, _ = sample_product  # price 12.90
        order, _ = create_paid_order(
            customer=sample_customer,
            items=[(sku, 3)],
            stripe_session_id="cs_test_2",
        )
        items = list(order.items.all())
        assert len(items) == 1
        assert items[0].unit_price == Decimal("12.90")
        assert items[0].subtotal == Decimal("38.70")

    def test_total_amount_computed_from_items(
        self, db, sample_customer, sample_product
    ):
        _, sku, _ = sample_product
        order, _ = create_paid_order(
            customer=sample_customer,
            items=[(sku, 3)],
            stripe_session_id="cs_test_3",
        )
        assert order.total_amount == Decimal("38.70")

    def test_creates_payment_record(self, db, sample_customer, sample_product):
        _, sku, _ = sample_product
        order, _ = create_paid_order(
            customer=sample_customer,
            items=[(sku, 2)],
            stripe_payment_intent="pi_test_4",
            stripe_session_id="cs_test_4",
        )
        payment = order.payment
        assert payment.status == "succeeded"
        assert payment.stripe_payment_intent == "pi_test_4"
        assert payment.amount == Decimal("25.80")
        assert payment.paid_at is not None

    def test_decrements_stock(self, db, sample_customer, sample_product):
        _, sku, stock = sample_product  # qty 50
        create_paid_order(
            customer=sample_customer,
            items=[(sku, 4)],
            stripe_session_id="cs_test_5",
        )
        stock.refresh_from_db()
        assert stock.quantity == 46

    def test_idempotent_on_session_id(self, db, sample_customer, sample_product):
        _, sku, stock = sample_product
        order1, created1 = create_paid_order(
            customer=sample_customer,
            items=[(sku, 4)],
            stripe_session_id="cs_dup",
        )
        order2, created2 = create_paid_order(
            customer=sample_customer,
            items=[(sku, 4)],
            stripe_session_id="cs_dup",
        )
        assert created1 is True
        assert created2 is False
        assert order1.pk == order2.pk
        assert order1.items.count() == 1
        stock.refresh_from_db()
        assert stock.quantity == 46  # decremented once, not twice

    def test_insufficient_stock_raises_and_rolls_back(
        self, db, sample_customer, sample_product
    ):
        from apps.checkout.models import Order

        _, sku, stock = sample_product  # qty 50
        with pytest.raises(ValueError):
            create_paid_order(
                customer=sample_customer,
                items=[(sku, 51)],
                stripe_session_id="cs_test_6",
            )
        stock.refresh_from_db()
        assert stock.quantity == 50  # unchanged
        assert not Order.objects.filter(stripe_session_id="cs_test_6").exists()

    def test_shipping_snapshot_persisted(self, db, sample_customer, sample_product):
        _, sku, _ = sample_product
        order, _ = create_paid_order(
            customer=sample_customer,
            items=[(sku, 1)],
            shipping=SHIPPING,
            stripe_session_id="cs_test_7",
        )
        order.refresh_from_db()
        assert order.shipping_first_name == "Marie"
        assert order.shipping_city == "Genève"
        assert order.shipping_country == "CH"
