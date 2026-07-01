"""
apps/b2b/tests/test_portal.py
=============================
L1 pro space: access control (no info leak), catalogue, 1-click reorder.
"""

import pytest
from django.urls import reverse

from apps.accounts.models import B2BAccount, Customer
from apps.b2b.models import B2BProductInfo, QuoteSimulation
from apps.checkout.models import Order, OrderItem
from decimal import Decimal

def make_b2b_customer(email="pro@test.com"):
    c = Customer.objects.create_user(
        email=email, password="StrongP@ss1!", customer_type="b2b_distributor",
    )
    account = B2BAccount.objects.create(customer=c, company_name="Dubno SA", status="active",)
    return c, account


@pytest.mark.django_db
class TestAccessControl:
    def test_non_pro_is_redirected(self, client):
        c = Customer.objects.create_user(email="b2c@test.com", password="StrongP@ss1!")
        client.force_login(c)
        resp = client.get(reverse("b2b:portal"))
        assert resp.status_code == 302  # silently redirected, no leak

    def test_pro_can_access_portal(self, client):
        c, _ = make_b2b_customer()
        client.force_login(c)
        assert client.get(reverse("b2b:portal")).status_code == 200


@pytest.mark.django_db
class TestCatalogueAndReorder:
    def test_catalogue_lists_b2b_products(self, client, sample_product):
        product, sku, _stock = sample_product
        B2BProductInfo.objects.create(sku=sku, moq=24, is_b2b_available=True)
        c, _ = make_b2b_customer()
        client.force_login(c)
        resp = client.get(reverse("b2b:catalogue"))
        assert resp.status_code == 200
        assert sku.sku_code.encode() in resp.content

    def test_reorder_creates_quote_simulation(self, client, sample_product):
        product, sku, _stock = sample_product
        c, account = make_b2b_customer()
        order = Order.objects.create(
            customer=c, order_number="B2B-0001",
            total_amount="100.00", channel="b2b",
        )
        # unit_price must be a Decimal: OrderItem.save() computes
        # subtotal = quantity * unit_price (string * int would repeat the text).
        # subtotal is recomputed in save(), so we don't pass it here.
        OrderItem.objects.create(
            order=order, sku=sku, quantity=2, unit_price=Decimal("10.00"),
        )
        client.force_login(c)
        resp = client.post(reverse("b2b:reorder", args=[order.id]))
        assert resp.status_code == 302
        assert QuoteSimulation.objects.filter(account=account).count() == 1