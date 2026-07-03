"""
apps/customer_area/tests/test_orders.py
=======================================
Tests for the customer area (dashboard, orders list, order detail, profile).

Key security property under test: a customer can only ever see their OWN
orders, never another customer's.
"""

import pytest
from django.urls import reverse

from apps.accounts.models import Customer
from apps.checkout.models import Order


@pytest.fixture
def customer_factory(db):
    """Create a customer with a known password."""

    def _make(email="c1@test.com", password="StrongP@ss123!", **kwargs):
        return Customer.objects.create_user(
            email=email,
            password=password,
            first_name=kwargs.pop("first_name", "Test"),
            last_name=kwargs.pop("last_name", "User"),
            **kwargs,
        )

    return _make


@pytest.fixture
def order_factory(db):
    """Create an order for a given customer."""

    def _make(customer, **kwargs):
        return Order.objects.create(
            customer=customer,
            order_number=Order.generate_order_number(),
            total_amount=kwargs.pop("total_amount", "29.90"),
            currency=kwargs.pop("currency", "EUR"),
            status=kwargs.pop("status", "pending"),
            **kwargs,
        )

    return _make


@pytest.mark.integration
class TestDashboard:
    def test_dashboard_requires_login(self, client, db):
        resp = client.get(reverse("customer_area:dashboard"))
        # @login_required redirects to login
        assert resp.status_code == 302
        assert "/accounts/login/" in resp.url

    def test_dashboard_shows_stats(self, client, customer_factory, order_factory):
        customer = customer_factory()
        order_factory(customer)
        order_factory(customer, status="paid")
        client.force_login(customer)

        resp = client.get(reverse("customer_area:dashboard"))
        assert resp.status_code == 200
        # 2 total orders shown
        assert b"2" in resp.content


@pytest.mark.integration
class TestOrdersList:
    def test_orders_list_shows_only_own_orders(
        self, client, customer_factory, order_factory
    ):
        alice = customer_factory(email="alice@test.com")
        bob = customer_factory(email="bob@test.com")
        alice_order = order_factory(alice)
        order_factory(bob)

        client.force_login(alice)
        resp = client.get(reverse("customer_area:orders"))

        assert resp.status_code == 200
        # Alice sees her order number
        assert alice_order.order_number.encode() in resp.content


@pytest.mark.integration
class TestOrderDetailSecurity:
    def test_cannot_access_another_customers_order(
        self, client, customer_factory, order_factory
    ):
        alice = customer_factory(email="alice2@test.com")
        bob = customer_factory(email="bob2@test.com")
        bob_order = order_factory(bob)

        client.force_login(alice)
        resp = client.get(reverse("customer_area:order_detail", args=[bob_order.id]))
        # Alice must be redirected away (cannot see Bob's order)
        assert resp.status_code == 302
        assert reverse("customer_area:orders") in resp.url

    def test_can_access_own_order(self, client, customer_factory, order_factory):
        alice = customer_factory(email="alice3@test.com")
        order = order_factory(alice)

        client.force_login(alice)
        resp = client.get(reverse("customer_area:order_detail", args=[order.id]))
        assert resp.status_code == 200
        assert order.order_number.encode() in resp.content


@pytest.mark.integration
class TestProfile:
    def test_profile_update(self, client, customer_factory):
        customer = customer_factory()
        client.force_login(customer)

        resp = client.post(
            reverse("customer_area:profile"),
            data={
                "first_name": "Updated",
                "last_name": "Name",
                "phone": "+41 79 000 00 00",
                "preferred_language": "en",
            },
        )
        assert resp.status_code == 302
        customer.refresh_from_db()
        assert customer.first_name == "Updated"
        assert customer.preferred_language == "en"
