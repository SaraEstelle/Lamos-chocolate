"""
apps/checkout/tests/test_emails.py
==================================
Tests for transactional emails (using Django's locmem backend).
"""

import pytest
from django.core import mail

from apps.checkout.models import Order
from apps.checkout.services import send_order_confirmation, send_order_shipped


@pytest.mark.integration
class TestTransactionalEmails:
    def test_order_confirmation_is_sent(self, customer_factory):
        customer = customer_factory(email="buyer@test.com")
        order = Order.objects.create(
            customer=customer,
            order_number=Order.generate_order_number(),
            total_amount="29.90", currency="EUR", status="paid",
        )
        send_order_confirmation(order)
        assert len(mail.outbox) == 1
        assert "buyer@test.com" in mail.outbox[0].to

    def test_order_shipped_is_sent(self, customer_factory):
        customer = customer_factory(email="ship@test.com")
        order = Order.objects.create(
            customer=customer,
            order_number=Order.generate_order_number(),
            total_amount="10.00", currency="EUR", status="shipped",
        )
        send_order_shipped(order)
        assert len(mail.outbox) == 1