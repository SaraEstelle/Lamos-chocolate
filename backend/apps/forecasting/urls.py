"""
apps/forecasting/urls.py
=========================
Routes de prévisions et alertes de stock.

Remarque :
Cette app n'a pas de routes publiques.
Elle fonctionne uniquement en arrière-plan (background tasks).

Contenu :
- Calcul des prévisions de ventes (forecasting/calculations.py)
- Alertes de stock bas (forecasting/alerts.py)
- Analytics et tendances (forecasting/analytics.py)

Ces opérations sont lancées :
- Automatiquement via Celery (tâches planifiées)
- Manuellement via la CLI Django ou l'admin
- Par webhook depuis l'application principale

Pas de routes HTTP nécessaires.
"""

# Nom de cette app
app_name = "forecasting"

# Cette app n'a pas de routes publiques
# Elle fonctionne uniquement en arrière-plan
urlpatterns = []
