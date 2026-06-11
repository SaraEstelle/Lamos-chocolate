"""
apps/customer_area/urls.py
===========================
Routes de l'espace client (mon compte, historique commandes).

Contenu :
- Tableau de bord (dashboard)
- Historique commandes (orders)
- Détail commande (order_detail)
- Gestion adresses (addresses)
- Profil client (profile)

Authentification : REQUISE
Seul l'utilisateur connecté peut accéder à ses données.
"""

from django.urls import path

# Nom de cette app
app_name = 'customer_area'

# Routes de l'espace client (authentifiées)
urlpatterns = [
    # path('', views.dashboard_view, name='dashboard'),                              # Tableau de bord
    # path('orders/', views.orders_view, name='orders'),                            # Historique commandes
    # path('orders/<uuid:order_id>/', views.order_detail_view, name='order_detail'),# Détail commande
    # path('addresses/', views.addresses_view, name='addresses'),                   # Gestion adresses
    # path('profile/', views.profile_view, name='profile'),                         # Profil client
]