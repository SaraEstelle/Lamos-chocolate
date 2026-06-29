"""Unit tests for the Stripe session-building layer (apps/checkout/stripe.py).

No real Stripe call is made: ``stripe.checkout.Session.create`` is patched. We
assert on the line items and metadata we hand to Stripe, because the webhook
reconstructs the order purely from that metadata (it has no Django session to
read).
"""

import json
from decimal import Decimal
from unittest.mock import patch

import pytest

from apps.checkout import stripe as checkout_stripe


def _cart_items(sample_product):
    """Build a one-line fake cart compatible with the stripe layer."""
    from apps.cart.cart import CartItem

    _, sku, _ = sample_product
    return [CartItem(sku=sku, quantity=2)]


@pytest.mark.django_db
class TestBuildLineItems:
    def test_amount_is_in_minor_units(self, sample_product):
        items = _cart_items(sample_product)
        line_items = checkout_stripe.build_line_items(items)
        assert len(line_items) == 1
        line = line_items[0]
        # 12.90 EUR -> 1290 cents
        assert line["price_data"]["unit_amount"] == 1290
        assert line["price_data"]["currency"] == "eur"
        assert line["quantity"] == 2

    def test_product_name_is_passed(self, sample_product):
        items = _cart_items(sample_product)
        line = checkout_stripe.build_line_items(items)[0]
        assert line["price_data"]["product_data"]["name"]


@pytest.mark.django_db
class TestBuildMetadata:
    def test_encodes_cart_customer_and_shipping(self, sample_product, sample_customer):
        _, sku, _ = sample_product
        items = _cart_items(sample_product)
        shipping = {"first_name": "Marie", "city": "Genève"}
        meta = checkout_stripe.build_metadata(
            customer=sample_customer,
            cart_items=items,
            shipping=shipping,
            currency="EUR",
            language="fr",
            channel="b2c",
        )
        assert meta["customer_id"] == str(sample_customer.id)
        assert json.loads(meta["cart"]) == {str(sku.id): 2}
        assert meta["currency"] == "EUR"
        assert meta["language"] == "fr"
        assert meta["channel"] == "b2c"
        assert meta["ship_first_name"] == "Marie"
        assert meta["ship_city"] == "Genève"


@pytest.mark.django_db
class TestCreateCheckoutSession:
    def test_calls_stripe_with_line_items_and_metadata(
        self, sample_product, sample_customer
    ):
        items = _cart_items(sample_product)
        with patch("stripe.checkout.Session.create") as mock_create:
            mock_create.return_value = type("S", (), {"id": "cs_test_1", "url": "https://stripe/cs_test_1"})()
            session = checkout_stripe.create_checkout_session(
                customer=sample_customer,
                cart_items=items,
                shipping={"first_name": "Marie"},
                currency="EUR",
                language="fr",
                channel="b2c",
                success_url="https://site/success",
                cancel_url="https://site/cancel",
            )
        assert session.id == "cs_test_1"
        kwargs = mock_create.call_args.kwargs
        assert kwargs["mode"] == "payment"
        assert kwargs["customer_email"] == sample_customer.email
        assert kwargs["success_url"] == "https://site/success"
        assert kwargs["cancel_url"] == "https://site/cancel"
        assert len(kwargs["line_items"]) == 1
        assert kwargs["metadata"]["customer_id"] == str(sample_customer.id)
