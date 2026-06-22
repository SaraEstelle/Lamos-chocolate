"""
apps/accounts/tests/test_data_foundations.py
============================================
Tests for the strategic data fields and B2BAccount.
"""

import pytest

from apps.accounts.models import B2BAccount, Customer


@pytest.mark.django_db
class TestCustomerStrategicFields:
    def test_defaults(self):
        c = Customer.objects.create_user(email="d@test.com", password="StrongP@ss1!")
        assert c.customer_type == "b2c"
        assert c.consent_nlpd is False
        assert c.canton == ""

    def test_can_set_canton_and_type(self):
        c = Customer.objects.create_user(
            email="vd@test.com", password="StrongP@ss1!",
            customer_type="b2b_distributor", canton="VD", npa="1004",
        )
        assert c.canton == "VD"
        assert c.customer_type == "b2b_distributor"


@pytest.mark.django_db
class TestB2BAccount:
    def test_create_b2b_account(self):
        c = Customer.objects.create_user(
            email="pro@test.com", password="StrongP@ss1!",
            customer_type="b2b_distributor",
        )
        account = B2BAccount.objects.create(
            customer=c, company_name="Dubno SA", segment="distributor",
        )
        assert account.customer == c
        assert str(account).startswith("Dubno SA")


@pytest.mark.django_db
class TestSKUMargin:
    def test_margin_computation(self, sample_product):
        # conftest's sample_product returns a (product, sku, stock) tuple.
        product, _sku, _stock = sample_product
        from apps.shop.models import SKU
        sku = SKU.objects.create(
            product=product, sku_code="TEST-1", format="bar",
            price="10.00", cost_chf="4.00",
        )
        assert abs(sku.margin - 0.6) < 0.001  # (10 - 4) / 10