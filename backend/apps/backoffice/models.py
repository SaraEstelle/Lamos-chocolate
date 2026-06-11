"""
apps/backoffice/models.py
==========================
Modèles du backoffice.

REMARQUE : Cette app n'a PAS de modèles propres.

Le backoffice (interface admin personnalisée) utilise
les modèles de TOUTES les autres apps :
- Customer (accounts)
- Product, Category, Stock (shop)
- Order, OrderItem, Payment (checkout)
- BusinessRequest (b2b)
- Forecast, Alert (forecasting)

C'est juste une interface de gestion.
Les modèles sont ailleurs.

Pas besoin de modèle = plus simple, moins de duplications.
"""

# Cette app n'a pas de modèles