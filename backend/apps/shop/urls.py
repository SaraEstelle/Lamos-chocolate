"""
apps/shop/urls.py
=================
Routes du catalogue produits (public, sans authentification).

- catalog        : listing des produits actifs (?category=<slug> optionnel)
- search         : recherche par nom/description (?q=)
- category       : produits d'une catégorie (par slug)
- product_detail : détail d'un produit (par slug)
"""

from django.urls import path

from apps.shop import views

app_name = "shop"

urlpatterns = [
    path("", views.CatalogView.as_view(), name="catalog"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("category/<slug:slug>/", views.CategoryView.as_view(), name="category"),
    path(
        "product/<slug:slug>/",
        views.ProductDetailView.as_view(),
        name="product_detail",
    ),
]
