"""
apps/backoffice/tests/test_backoffice.py
========================================
Tests for the staff-only backoffice.
"""

import pytest
from django.urls import reverse

from apps.checkout.models import Order


@pytest.fixture
def staff_customer(db):
    """A staff customer who can access the backoffice."""
    from apps.accounts.models import Customer

    return Customer.objects.create_user(
        email="staff@test.com",
        password="StrongP@ss123!",
        first_name="Staff",
        last_name="User",
        is_staff=True,
    )


@pytest.mark.integration
class TestBackofficeAccess:
    def test_dashboard_denied_for_anonymous(self, client, db):
        resp = client.get(reverse("backoffice:dashboard"))
        assert resp.status_code in (302, 403)  # redirected to admin login

    def test_dashboard_denied_for_non_staff(self, client, customer_factory):
        client.force_login(customer_factory())
        resp = client.get(reverse("backoffice:dashboard"))
        assert resp.status_code in (302, 403)

    def test_dashboard_ok_for_staff(self, client, staff_customer):
        client.force_login(staff_customer)
        resp = client.get(reverse("backoffice:dashboard"))
        assert resp.status_code == 200


@pytest.mark.integration
class TestOrderStatusUpdate:
    def test_staff_can_update_order_status(
        self, client, staff_customer, customer_factory
    ):
        order = Order.objects.create(
            customer=customer_factory(),
            order_number=Order.generate_order_number(),
            total_amount="10.00",
            currency="EUR",
            status="pending",
        )
        client.force_login(staff_customer)
        resp = client.post(
            reverse("backoffice:order_status", args=[order.id]),
            data={"status": "shipped"},
        )
        assert resp.status_code == 302
        order.refresh_from_db()
        assert order.status == "shipped"


@pytest.mark.integration
class TestForecastingView:
    def test_forecasting_denied_for_non_staff(self, client, customer_factory):
        client.force_login(customer_factory())
        resp = client.get(reverse("backoffice:forecasting"))
        assert resp.status_code in (302, 403)

    def test_forecasting_ok_for_staff(self, client, staff_customer):
        client.force_login(staff_customer)
        resp = client.get(reverse("backoffice:forecasting"))
        assert resp.status_code == 200
