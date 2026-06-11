"""
apps/backoffice/urls.py
=======================
Routes de l'admin personnalisé (backoffice).

Contenu :
- Tableau de bord admin (dashboard)
- Gestion produits (products)
- Gestion stocks (stocks)
- Gestion commandes (orders)
- Gestion clients (customers)
- Analytics et reports

Authentification : REQUISE (superuser/staff seulement)
@login_required + @staff_member_required

Différence avec /admin/ :
- /admin/         → Interface Django Admin (générique)
- /backoffice/    → Interface personnalisée (custom)

Cette interface est réservée au personnel Lamos Chocolate.
"""

from django.urls import path

# Nom de cette app
app_name = 'backoffice'

# Routes du backoffice (staff/superuser seulement)
urlpatterns = [
    # path('', views.dashboard_view, name='dashboard'),                         # Tableau de bord
    # path('products/', views.products_view, name='products'),                 # Gestion produits
    # path('products/create/', views.create_product_view, name='create_product'), # Créer produit
    # path('products/<uuid:product_id>/edit/', views.edit_product_view, name='edit_product'), # Éditer
    # path('stocks/', views.stocks_view, name='stocks'),                       # Gestion stocks
    # path('orders/', views.orders_view, name='orders'),                       # Gestion commandes
    # path('customers/', views.customers_view, name='customers'),             # Gestion clients
    # path('analytics/', views.analytics_view, name='analytics'),             # Analytics
]