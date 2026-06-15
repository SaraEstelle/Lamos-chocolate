"""
apps/shop/selectors.py
======================
Read-only query helpers for the catalog (data access layer).

Product queries eager-load related categories, SKUs, stock and images to
avoid N+1 queries when the templates iterate over them.
"""

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from apps.shop.models import Category, Product


def get_active_products() -> QuerySet[Product]:
    """Return active products eager-loaded for catalog display."""
    return (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("skus__stock", "images")
    )


def get_product_by_slug(slug: str) -> Product:
    """Return an active product by slug, or raise ``Http404``."""
    return get_object_or_404(
        Product.objects.select_related("category").prefetch_related(
            "skus__stock", "images"
        ),
        slug=slug,
        is_active=True,
    )


def get_category_by_slug(slug: str) -> Category:
    """Return a category by slug, or raise ``Http404``."""
    return get_object_or_404(Category, slug=slug)


def get_all_categories() -> QuerySet[Category]:
    """Return all categories, used for filter navigation."""
    return Category.objects.all()
