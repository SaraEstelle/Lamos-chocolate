"""Tests for shop catalog filtering and search helpers."""

import pytest

from apps.shop import filters, selectors


@pytest.fixture
def catalog(db, sample_category):
    """Two active products (FR/EN names + descriptions) and one inactive."""
    from apps.shop.models import Product

    Product.objects.create(
        slug="dark-bar",
        name_fr="Tablette Noire",
        name_en="Dark Bar",
        description_fr="cacao intense",
        description_en="intense cocoa",
        category=sample_category,
    )
    Product.objects.create(
        slug="milk-bar",
        name_fr="Tablette Lait",
        name_en="Milk Bar",
        description_fr="onctueux",
        description_en="creamy",
        category=sample_category,
    )
    Product.objects.create(
        slug="hidden",
        name_fr="Caché",
        name_en="Hidden",
        category=sample_category,
        is_active=False,
    )


class TestSearchProducts:
    def test_matches_french_name(self, catalog):
        qs = filters.search_products(selectors.get_active_products(), "Noire")
        assert set(qs.values_list("slug", flat=True)) == {"dark-bar"}

    def test_matches_english_name(self, catalog):
        qs = filters.search_products(selectors.get_active_products(), "Milk")
        assert set(qs.values_list("slug", flat=True)) == {"milk-bar"}

    def test_matches_description(self, catalog):
        qs = filters.search_products(selectors.get_active_products(), "cocoa")
        assert set(qs.values_list("slug", flat=True)) == {"dark-bar"}

    def test_empty_query_returns_all_active(self, catalog):
        qs = filters.search_products(selectors.get_active_products(), "")
        assert qs.count() == 2

    def test_no_match(self, catalog):
        qs = filters.search_products(selectors.get_active_products(), "zzzzz")
        assert qs.count() == 0


class TestFilterByCategory:
    def test_filter_by_existing_category(self, catalog, sample_category):
        qs = filters.filter_by_category(
            selectors.get_active_products(), sample_category.slug
        )
        assert qs.count() == 2

    def test_filter_by_unknown_category(self, catalog):
        qs = filters.filter_by_category(selectors.get_active_products(), "nope")
        assert qs.count() == 0

    def test_no_slug_returns_all(self, catalog):
        qs = filters.filter_by_category(selectors.get_active_products(), "")
        assert qs.count() == 2
