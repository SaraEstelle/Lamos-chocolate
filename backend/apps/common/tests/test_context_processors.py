"""Tests for shared template context processors."""

from decimal import Decimal

from django.contrib.sessions.backends.db import SessionStore

from apps.cart.services import add_to_cart
from apps.common.context_processors import cart_summary


def _request_with_session(rf):
    request = rf.get("/")
    request.session = SessionStore()
    return request


class TestCartSummary:
    def test_empty_cart(self, db, rf):
        request = _request_with_session(rf)
        ctx = cart_summary(request)
        assert ctx["cart_count"] == 0
        assert ctx["cart_total"] == Decimal("0.00")

    def test_counts_units_and_total(self, db, rf, sample_product):
        from apps.cart.cart import Cart

        _, sku, _ = sample_product  # price 12.90
        request = _request_with_session(rf)
        add_to_cart(Cart(request), sku.id, 2)

        ctx = cart_summary(request)
        assert ctx["cart_count"] == 2
        assert ctx["cart_total"] == Decimal("25.80")
