"""HTTP tests for the checkout page (GET).

The checkout view shows the order summary and the shipping form. It requires an
authenticated customer and a non-empty cart; otherwise it redirects.
"""

from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse


def _fill_cart(client, sku, quantity=2):
    session = client.session
    session["cart"] = {str(sku.id): {"quantity": quantity}}
    session.save()


_VALID_SHIPPING = {
    "first_name": "Marie",
    "last_name": "Test",
    "address1": "1 rue du Test",
    "address2": "",
    "city": "Genève",
    "postal_code": "1200",
    "country": "CH",
}


@pytest.mark.django_db
class TestCheckoutView:
    def test_redirects_anonymous_to_login(self, client):
        resp = client.get(reverse("checkout:checkout"))
        assert resp.status_code == 302
        assert reverse("accounts:login") in resp.url

    def test_empty_cart_redirects_to_cart(self, client, sample_customer):
        client.force_login(sample_customer)
        resp = client.get(reverse("checkout:checkout"))
        assert resp.status_code == 302
        assert resp.url == reverse("cart:view")

    def test_renders_with_items(self, client, sample_customer, sample_product):
        _, sku, _ = sample_product
        client.force_login(sample_customer)
        _fill_cart(client, sku, quantity=2)
        resp = client.get(reverse("checkout:checkout"))
        assert resp.status_code == 200
        assert "checkout/checkout.html" in [t.name for t in resp.templates]
        assert "form" in resp.context
        assert resp.context["cart_total"] == Decimal("25.80")

    def test_form_prefilled_with_customer_name(
        self, client, sample_customer, sample_product
    ):
        _, sku, _ = sample_product
        client.force_login(sample_customer)
        _fill_cart(client, sku)
        resp = client.get(reverse("checkout:checkout"))
        form = resp.context["form"]
        assert form.initial.get("first_name") == sample_customer.first_name
        assert form.initial.get("last_name") == sample_customer.last_name


@pytest.mark.django_db
class TestCreateCheckoutSessionView:
    def test_anonymous_redirects_to_login(self, client):
        resp = client.post(reverse("checkout:create_session"), _VALID_SHIPPING)
        assert resp.status_code == 302
        assert reverse("accounts:login") in resp.url

    def test_empty_cart_redirects_to_cart(self, client, sample_customer):
        client.force_login(sample_customer)
        resp = client.post(reverse("checkout:create_session"), _VALID_SHIPPING)
        assert resp.status_code == 302
        assert resp.url == reverse("cart:view")

    def test_invalid_form_rerenders_checkout(
        self, client, sample_customer, sample_product
    ):
        _, sku, _ = sample_product
        client.force_login(sample_customer)
        _fill_cart(client, sku)
        bad = {**_VALID_SHIPPING, "postal_code": ""}
        resp = client.post(reverse("checkout:create_session"), bad)
        assert resp.status_code == 200
        assert "checkout/checkout.html" in [t.name for t in resp.templates]
        assert resp.context["form"].errors

    def test_valid_form_redirects_to_stripe(
        self, client, sample_customer, sample_product
    ):
        _, sku, _ = sample_product
        client.force_login(sample_customer)
        _fill_cart(client, sku)
        fake_session = type("S", (), {"id": "cs_1", "url": "https://stripe/cs_1"})()
        with patch(
            "apps.checkout.views.create_checkout_session", return_value=fake_session
        ) as mock_create:
            resp = client.post(reverse("checkout:create_session"), _VALID_SHIPPING)
        assert resp.status_code == 302
        assert resp.url == "https://stripe/cs_1"
        assert mock_create.call_args.kwargs["customer"] == sample_customer


@pytest.mark.django_db
class TestSuccessCancelViews:
    def test_success_clears_cart(self, client, sample_product):
        _, sku, _ = sample_product
        _fill_cart(client, sku)
        resp = client.get(reverse("checkout:success"))
        assert resp.status_code == 200
        assert client.session.get("cart") == {}

    def test_cancel_keeps_cart(self, client, sample_product):
        _, sku, _ = sample_product
        _fill_cart(client, sku)
        resp = client.get(reverse("checkout:cancel"))
        assert resp.status_code == 200
        assert client.session["cart"] == {str(sku.id): {"quantity": 2}}
