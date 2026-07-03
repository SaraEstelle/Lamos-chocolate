"""Tests for shop catalog views (catalog, category, search, detail)."""

import pytest
from django.urls import reverse


@pytest.fixture
def products(db, sample_category):
    """Three active products (each with one in-stock SKU) and one inactive."""
    from apps.shop.models import SKU, Product, Stock

    items = []
    for i in range(3):
        product = Product.objects.create(
            slug=f"prod-{i}",
            name_fr=f"Produit {i}",
            name_en=f"Product {i}",
            category=sample_category,
        )
        sku = SKU.objects.create(
            product=product, sku_code=f"SKU-{i}", format="Bar 100g", price="10.00"
        )
        Stock.objects.create(sku=sku, quantity=20)
        items.append(product)

    inactive = Product.objects.create(
        slug="inactive",
        name_fr="Inactif",
        name_en="Inactive",
        category=sample_category,
        is_active=False,
    )
    return items, inactive


class TestCatalogView:
    def test_lists_only_active_products(self, client, products):
        response = client.get(reverse("shop:catalog"))
        content = response.content.decode()
        assert response.status_code == 200
        assert "Produit 0" in content
        assert "Inactif" not in content

    def test_pagination_caps_at_twelve(self, client, db, sample_category):
        from apps.shop.models import Product

        for i in range(15):
            Product.objects.create(
                slug=f"p-{i}",
                name_fr=f"P{i}",
                name_en=f"P{i}",
                category=sample_category,
            )
        response = client.get(reverse("shop:catalog"))
        assert response.context["is_paginated"] is True
        assert len(response.context["products"]) == 12

    def test_filter_by_category_query_param(self, client, products, sample_category):
        response = client.get(
            reverse("shop:catalog"), {"category": sample_category.slug}
        )
        assert response.status_code == 200
        assert len(response.context["products"]) == 3


class TestCategoryView:
    def test_lists_category_products(self, client, products, sample_category):
        response = client.get(
            reverse("shop:category", kwargs={"slug": sample_category.slug})
        )
        assert response.status_code == 200
        assert len(response.context["products"]) == 3
        assert response.context["category"] == sample_category

    def test_unknown_category_returns_404(self, client, db):
        response = client.get(reverse("shop:category", kwargs={"slug": "nope"}))
        assert response.status_code == 404


class TestSearchView:
    def test_search_matches_name(self, client, products):
        response = client.get(reverse("shop:search"), {"q": "Produit 1"})
        content = response.content.decode()
        assert response.status_code == 200
        assert "Produit 1" in content

    def test_empty_query_returns_all_active(self, client, products):
        response = client.get(reverse("shop:search"), {"q": ""})
        assert len(response.context["products"]) == 3


class TestProductDetailView:
    def test_active_product_returns_200(self, client, products):
        response = client.get(reverse("shop:product_detail", kwargs={"slug": "prod-0"}))
        assert response.status_code == 200
        assert "Produit 0" in response.content.decode()

    def test_inactive_product_returns_404(self, client, products):
        response = client.get(
            reverse("shop:product_detail", kwargs={"slug": "inactive"})
        )
        assert response.status_code == 404

    def test_unknown_slug_returns_404(self, client, products):
        response = client.get(
            reverse("shop:product_detail", kwargs={"slug": "does-not-exist"})
        )
        assert response.status_code == 404

    def test_context_exposes_active_skus(self, client, products):
        response = client.get(reverse("shop:product_detail", kwargs={"slug": "prod-0"}))
        assert len(response.context["skus"]) == 1
