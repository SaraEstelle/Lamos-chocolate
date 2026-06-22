"""
apps/shop/tests/test_catalog_update.py
======================================
Defensive tests for the final catalog (and the Nestlé trademark ban).
"""

import pytest

from apps.shop.models import Category, Product, SKU


@pytest.mark.django_db
class TestNewCatalog:
    def test_three_b2c_families_loaded(self):
        # loaddata works inside tests via the django_db fixture + call_command
        from django.core.management import call_command
        call_command("loaddata", "categories", "products", "skus", verbosity=0)
        assert Category.objects.count() == 3
        assert Product.objects.filter(slug="kunafa").exists()
        assert SKU.objects.filter(product__slug="kunafa").count() == 4

    def test_no_forbidden_after_eight_name(self):
        # Even on an empty DB this must never regress once products exist.
        for p in Product.objects.all():
            assert "after eight" not in p.name_fr.lower()
            assert "after eight" not in p.name_en.lower()