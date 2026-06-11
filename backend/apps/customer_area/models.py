"""
apps/customer_area/models.py
=============================
Modèles de l'espace client.

REMARQUE : Cette app n'a PAS de modèles propres.

Elle utilise les modèles des autres apps :
- Order (apps.checkout.models)
- OrderItem (apps.checkout.models)
- Payment (apps.checkout.models)
- Customer (apps.accounts.models)

L'espace client est juste une interface pour afficher
les commandes et informations du client.

Pas besoin de modèle = moins de migrations, plus simple.
"""

# Cette app n'a pas de modèles