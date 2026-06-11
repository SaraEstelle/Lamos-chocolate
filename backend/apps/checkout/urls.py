"""
apps/checkout/urls.py
=====================
Routes du paiement et commandes.

Contenu :
- Checkout (checkout_view) — page de paiement
- Succès de paiement (success)
- Annulation de paiement (cancel)
- Webhook Stripe (webhook) — route publique, sans i18n

Sécurité :
- Webhook Stripe est PUBLIC (sans authentification)
- Webhook Stripe n'a pas de CSRF (Stripe envoie une signature)
- Vérifier TOUJOURS la signature Stripe avec stripe.Webhook.construct_event()

Règulation Suisse (RGPD) :
- Toutes les données de paiement sont cryptées
- Pas d'stockage des données de carte bancaire (PCI-DSS)
- Utiliser Stripe comme intermédiaire de confiance
"""

from django.urls import path

# Nom de cette app
app_name = 'checkout'

# Routes du paiement
urlpatterns = [
    # path('', views.checkout_view, name='checkout'),           # Page de paiement
    # path('success/', views.success_view, name='success'),     # Paiement réussi
    # path('cancel/', views.cancel_view, name='cancel'),        # Paiement annulé
    # path('webhook/', views.webhook_view, name='webhook'),     # Webhook Stripe (sans CSRF)
]