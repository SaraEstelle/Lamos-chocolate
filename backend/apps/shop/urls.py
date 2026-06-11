"""
apps/shop/urls.py
=================
Routes du catalogue produits.

Contenu :
- Listing produits (catalog)
- Détail produit (product_detail)
- Catégories (categories)
- Recherche (search)
- Filtrage (filters)

Cette app ne nécessite pas d'authentification.
Affichage public du catalogue.
"""

from django.urls import path

# Nom de cette app
app_name = 'shop'

# Routes du catalogue
urlpatterns = [
    # path('', views.catalog_view, name='catalog'),                           # Listing produits
    # path('product/<slug:slug>/', views.product_detail_view, name='detail'), # Détail produit
    # path('category/<slug:slug>/', views.category_view, name='category'),    # Produits d'une catégorie
    # path('search/', views.search_view, name='search'),                      # Recherche
]