"""
apps/cart/urls.py
=================
Routes du panier (shopping cart).

Contenu :
- Voir le panier (view_cart)
- Ajouter au panier (add_item) — AJAX
- Retirer du panier (remove_item) — AJAX
- Mettre à jour la quantité (update_quantity) — AJAX

AJAX = Requête asynchrone JavaScript
Les routes AJAX ne sont pas dans i18n_patterns
pour avoir des URLs uniformes (/api/cart/add/)
"""

from django.urls import path

# Nom de cette app
app_name = 'cart'

# Routes du panier
urlpatterns = [
    # path('', views.view_cart, name='view'),                                  # Voir le panier
    # path('add/', views.add_to_cart, name='add'),                            # Ajouter au panier (AJAX)
    # path('remove/<uuid:item_id>/', views.remove_from_cart, name='remove'),  # Retirer (AJAX)
    # path('update/<uuid:item_id>/', views.update_quantity, name='update'),   # Mettre à jour (AJAX)
]