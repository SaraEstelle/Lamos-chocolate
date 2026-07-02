"""
apps/checkout/tests/test_selectors.py
=====================================
Single source of truth for realised revenue by channel, shared by the
backoffice dashboard and the executive cockpit.
"""

import pytest

from apps.accounts.models import Customer
from apps.checkout.models import Order
from apps.checkout.selectors import (
    PAID_STATUSES,
    channel_revenue,
    revenue_by_channel,
)


def make_order(customer, channel, amount, status="paid", number="LM-TEST-1"):
    return Order.objects.create(
        customer=customer,
        order_number=number,
        total_amount=amount,
        status=status,
        channel=channel,
    )


@pytest.mark.django_db
class TestChannelRevenue:

    def _customer(self):
        return Customer.objects.create_user(
            email="buyer@test.com", password="StrongP@ss1!",
        )

    def test_channel_revenue_sums_only_paid_orders(self):
        c = self._customer()
        make_order(c, "b2b", 100, status="paid", number="LM-1")
        make_order(c, "b2b", 50, status="shipped", number="LM-2")   # counts
        make_order(c, "b2b", 999, status="pending", number="LM-3")  # ignored
        make_order(c, "b2c", 30, status="paid", number="LM-4")

        assert channel_revenue("b2b") == 150
        assert channel_revenue("b2c") == 30

    def test_channel_revenue_zero_when_no_orders(self):
        self._customer()
        assert channel_revenue("b2b") == 0

    def test_revenue_by_channel_splits_and_orders(self):
        c = self._customer()
        make_order(c, "b2b", 100, number="LM-A")
        make_order(c, "b2b", 40, number="LM-B")
        make_order(c, "b2c", 60, number="LM-C")

        rows = {r["channel"]: r for r in revenue_by_channel()}
        assert rows["b2b"]["revenue"] == 140
        assert rows["b2b"]["orders"] == 2
        assert rows["b2c"]["revenue"] == 60

    def test_pending_status_not_in_paid_statuses(self):
        # Guards the canonical definition the cockpit relies on.
        assert "pending" not in PAID_STATUSES
        assert set(PAID_STATUSES) == {"paid", "processing", "shipped", "delivered"}
