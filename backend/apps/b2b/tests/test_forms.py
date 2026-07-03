"""
apps/b2b/tests/test_forms.py
============================
B2BRequestForm (honeypot, validation) + ConfiguratorForm (B2B-only SKUs).
"""

import pytest

from apps.b2b.forms import B2BRequestForm, ConfiguratorForm
from apps.b2b.models import B2BProductInfo

VALID = {
    "company_name": "Hotel Beau-Rivage",
    "contact_name": "Jean Dupont",
    "contact_email": "jean@beaurivage.ch",
    "contact_phone": "+41 22 000 00 00",
    "sector": "Hospitality",
    "estimated_qty": 200,
    "occasion": "Christmas",
    "message": "We need branded chocolates.",
}


class TestB2BRequestForm:
    def test_valid(self):
        form = B2BRequestForm(data={**VALID, "website": ""})
        assert form.is_valid(), form.errors
        assert form.is_bot() is False

    def test_honeypot_marks_bot(self):
        form = B2BRequestForm(data={**VALID, "website": "http://spam"})
        assert form.is_valid()
        assert form.is_bot() is True

    def test_quantity_must_be_positive(self):
        form = B2BRequestForm(data={**VALID, "estimated_qty": 0, "website": ""})
        assert not form.is_valid()
        assert "estimated_qty" in form.errors


@pytest.mark.django_db
class TestConfiguratorForm:
    def test_only_b2b_skus_allowed(self, sample_product):
        product, sku, _stock = sample_product
        B2BProductInfo.objects.create(sku=sku, moq=24, is_b2b_available=True)
        form = ConfiguratorForm()
        assert sku in form.fields["sku"].queryset
