"""Unit tests for the session cart and its services."""

from decimal import Decimal

import pytest

from apps.cart.cart import Cart
from apps.cart.services import (
    add_to_cart,
    calculate_total,
    remove_from_cart,
    update_quantity,
)


@pytest.fixture
def cart(rf):
    """A Cart backed by a real (in-memory) session on a dummy request."""
    from django.contrib.sessions.backends.db import SessionStore

    request = rf.get("/cart/")
    request.session = SessionStore()
    return Cart(request)


class TestAddToCart:
    def test_add_single_item(self, db, cart, sample_product):
        _, sku, _ = sample_product
        add_to_cart(cart, sku.id, 2)
        assert len(cart) == 2
        assert cart.get_quantity(sku.id) == 2

    def test_add_accumulates_quantity(self, db, cart, sample_product):
        _, sku, _ = sample_product
        add_to_cart(cart, sku.id, 2)
        add_to_cart(cart, sku.id, 3)
        assert cart.get_quantity(sku.id) == 5

    def test_add_unknown_sku_raises(self, db, cart):
        with pytest.raises(ValueError, match="not found or inactive"):
            add_to_cart(cart, 999999, 1)

    def test_add_zero_quantity_raises(self, db, cart, sample_product):
        _, sku, _ = sample_product
        with pytest.raises(ValueError, match="positive integer"):
            add_to_cart(cart, sku.id, 0)

    def test_add_beyond_stock_raises(self, db, cart, sample_product):
        _, sku, _ = sample_product
        with pytest.raises(ValueError, match="Insufficient stock"):
            add_to_cart(cart, sku.id, 51)


class TestUpdateQuantity:
    def test_update_sets_absolute_quantity(self, db, cart, sample_product):
        _, sku, _ = sample_product
        add_to_cart(cart, sku.id, 2)
        update_quantity(cart, sku.id, 5)
        assert cart.get_quantity(sku.id) == 5

    def test_update_to_zero_removes_line(self, db, cart, sample_product):
        _, sku, _ = sample_product
        add_to_cart(cart, sku.id, 2)
        update_quantity(cart, sku.id, 0)
        assert sku.id not in cart


class TestRemoveAndTotal:
    def test_remove_drops_line(self, db, cart, sample_product):
        _, sku, _ = sample_product
        add_to_cart(cart, sku.id, 2)
        remove_from_cart(cart, sku.id)
        assert cart.is_empty

    def test_calculate_total(self, db, cart, sample_product):
        _, sku, _ = sample_product  # price 12.90
        add_to_cart(cart, sku.id, 3)
        assert calculate_total(cart) == Decimal("38.70")

    def test_iter_yields_cart_items(self, db, cart, sample_product):
        _, sku, _ = sample_product
        add_to_cart(cart, sku.id, 2)
        items = list(cart)
        assert len(items) == 1
        assert items[0].sku.id == sku.id
        assert items[0].subtotal == Decimal("25.80")
