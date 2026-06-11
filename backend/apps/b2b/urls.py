"""
apps/b2b/urls.py
================
Routes du portail B2B (business-to-business).

Contenu :
- Présentation B2B (presentation)
- Formulaire de demande (request_form)
- Liste des demandes (requests_list)
- Détail demande (request_detail)
- Devis (quote_request)

Authentification : OPTIONNELLE
Les visiteurs non authentifiés peuvent soumettre une demande.
Les clients B2B authentifiés voient leur historique.

Règulation Suisse (RGPD) :
- Consentement explicite pour recevoir des communications marketing
- Droit d'opposition au traitement des données
- Durée de conservation limitée (3 ans max)
"""

from django.urls import path

# Nom de cette app
app_name = 'b2b'

# Routes du portail B2B
urlpatterns = [
    # path('', views.presentation_view, name='presentation'),                    # Présentation B2B
    # path('request/', views.request_form_view, name='request'),                # Formulaire de demande
    # path('requests/', views.requests_list_view, name='requests_list'),        # Historique demandes
    # path('requests/<uuid:request_id>/', views.request_detail_view, name='detail'), # Détail demande
    # path('quote/', views.quote_request_view, name='quote'),                   # Formulaire de devis
]