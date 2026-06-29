"""Tests for the Stripe webhook (apps/checkout/webhooks.py).

The signature check is patched (``stripe.Webhook.construct_event``) so we never
need a real signing secret. We assert the webhook turns a
``checkout.session.completed`` event into a paid order via ``create_paid_order``
and stays idempotent on redelivery.
"""

import json
from decimal import Decimal
from unittest.mock import patch

import pytest
import stripe

from apps.checkout.models import Order


def _event(session):
    return {"type": "checkout.session.completed", "data": {"object": session}}


def _session(sku, customer, session_id="cs_test_1"):
    return {
        "id": session_id,
        "payment_intent": "pi_test_1",
        "metadata": {
            "customer_id": str(customer.id),
            "cart": json.dumps({str(sku.id): 2}),
            "currency": "EUR",
            "language": "fr",
            "channel": "b2c",
            "ship_first_name": "Marie",
            "ship_last_name": "Test",
            "ship_address1": "1 rue du Test",
            "ship_city": "Genève",
            "ship_postal_code": "1200",
            "ship_country": "CH",
        },
    }


@pytest.mark.django_db
class TestStripeWebhook:
    def _post(self, client):
        return client.post(
            "/checkout/webhook/",
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=1,v1=sig",
        )

    def test_invalid_signature_returns_400(self, client):
        with patch(
            "stripe.Webhook.construct_event",
            side_effect=stripe.error.SignatureVerificationError("bad", "sig"),
        ):
            resp = self._post(client)
        assert resp.status_code == 400
        assert Order.objects.count() == 0

    def test_malformed_payload_returns_400(self, client):
        with patch(
            "stripe.Webhook.construct_event", side_effect=ValueError("bad json")
        ):
            resp = self._post(client)
        assert resp.status_code == 400

    def test_completed_session_creates_paid_order(
        self, client, sample_product, sample_customer
    ):
        _, sku, stock = sample_product
        event = _event(_session(sku, sample_customer))
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch("apps.checkout.webhooks.send_order_confirmation") as mock_email:
                resp = self._post(client)
        assert resp.status_code == 200
        order = Order.objects.get(stripe_session_id="cs_test_1")
        assert order.status == "paid"
        assert order.total_amount == Decimal("25.80")
        assert order.shipping_city == "Genève"
        assert order.items.count() == 1
        stock.refresh_from_db()
        assert stock.quantity == 48  # 50 - 2
        mock_email.assert_called_once()

    def test_redelivered_event_is_idempotent(
        self, client, sample_product, sample_customer
    ):
        _, sku, _ = sample_product
        event = _event(_session(sku, sample_customer))
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch("apps.checkout.webhooks.send_order_confirmation"):
                self._post(client)
                self._post(client)
        assert Order.objects.filter(stripe_session_id="cs_test_1").count() == 1

    def test_unhandled_event_type_is_ignored(self, client):
        event = {"type": "payment_intent.created", "data": {"object": {}}}
        with patch("stripe.Webhook.construct_event", return_value=event):
            resp = self._post(client)
        assert resp.status_code == 200
        assert Order.objects.count() == 0
