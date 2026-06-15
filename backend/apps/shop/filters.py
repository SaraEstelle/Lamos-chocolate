"""
apps/shop/filters.py
====================
Catalog filtering and search helpers operating on a Product queryset.

Each helper is a no-op when its argument is empty, so they can be chained
freely from the views.
"""

from django.db.models import Q, QuerySet


def filter_by_category(queryset: QuerySet, category_slug: str) -> QuerySet:
    """Restrict products to a given category slug."""
    if not category_slug:
        return queryset
    return queryset.filter(category__slug=category_slug)


def search_products(queryset: QuerySet, query: str) -> QuerySet:
    """Filter products matching the query on FR/EN name and description."""
    if not query:
        return queryset
    return queryset.filter(
        Q(name_fr__icontains=query)
        | Q(name_en__icontains=query)
        | Q(description_fr__icontains=query)
        | Q(description_en__icontains=query)
    )
