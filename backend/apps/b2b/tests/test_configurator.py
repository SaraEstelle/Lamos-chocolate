"""
apps/b2b/tests/test_configurator.py
===================================
L2 configurator: MOQ simulation + quote request.
"""

import pytest
from django.urls import reverse

from apps.accounts.models import B2BAccount, Customer
from apps.b2b.models import B2BProductInfo, CustomizationRequest, QuoteSimulation


@pytest.fixture
def pro_with_sku(sample_product):
    product, sku, _stock = sample_product
    B2BProductInfo.objects.create(
        sku=sku, moq=24, is_b2b_available=True, b2b_unit_price="5.00",
    )
    c = Customer.objects.create_user(
        email="conf@test.com", password="StrongP@ss1!", customer_type="b2b_hospitality",
    )
    account = B2BAccount.objects.create(customer=c, company_name="Hotel X", status="active",)
    return c, account, sku


@pytest.mark.django_db
class TestConfigurator:
    def test_simulate_above_moq(self, client, pro_with_sku):
        c, account, sku = pro_with_sku
        client.force_login(c)
        resp = client.post(reverse("b2b:configurator"), data={
            "sku": sku.pk, "quantity": 50, "action": "simulate",
        })
        assert resp.status_code == 200
        sim = QuoteSimulation.objects.filter(account=account).latest("created_at")
        assert sim.moq_reached is True  # 50 >= 24

    def test_simulate_below_moq(self, client, pro_with_sku):
        c, account, sku = pro_with_sku
        client.force_login(c)
        client.post(reverse("b2b:configurator"), data={
            "sku": sku.pk, "quantity": 10, "action": "simulate",
        })
        sim = QuoteSimulation.objects.filter(account=account).latest("created_at")
        assert sim.moq_reached is False  # 10 < 24

    def test_request_quote_creates_customization_and_email(self, client, pro_with_sku, mailoutbox):
        c, account, sku = pro_with_sku
        client.force_login(c)
        resp = client.post(reverse("b2b:configurator"), data={
            "sku": sku.pk, "quantity": 50, "action": "request_quote",
            "logo_engraved": "on", "inner_packaging": "Gold box",
        })
        assert resp.status_code == 302
        assert CustomizationRequest.objects.filter(
            account=account, status="quote",
        ).count() == 1
        assert len(mailoutbox) == 1  # sales notified