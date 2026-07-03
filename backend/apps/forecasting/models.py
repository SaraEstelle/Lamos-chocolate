"""
apps/forecasting/models.py
===========================
Modèles de prévisions de ventes et alertes de stock.

Modèles :
1. Forecast — Prévision de ventes pour un produit
2. Alert — Alerte basée sur une prévision

Qu'est-ce que c'est ?
La prévision utilise les données de ventes passées pour prédire
les ventes futures. Ex :
- "Le chocolat noir vendra 150 unités le mois prochain"
- "La truffe noisette vendra 80 unités"

Les alertes avertissent si le stock est trop bas.

Calcul des prévisions :
- Moyenne des ventes passées (3 mois, 6 mois, 1 an)
- Tendances saisonnières (Noël = plus ventes)
- Machine Learning (optionnel, phase 2)

Utilisation :
- Optimiser le stock (acheter juste assez)
- Prédire les ruptures de stock
- Planifier la production
"""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.shop.models import Product


class Forecast(models.Model):
    """
    Prévision de ventes pour un produit.

    Exemple :
    - Product = Chocolat noir 70%
    - forecast_date = 2026-07-01
    - predicted_quantity = 150 (unités estimées)
    - confidence_score = 0.92 (92% de confiance)

    Champs :
    - product : Produit
    - forecast_date : Date de la prévision
    - predicted_quantity : Quantité prédite
    - confidence_score : Niveau de confiance (0 à 1)
    - created_at : Date du calcul
    """

    # Identifiant
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Produit
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="forecasts", help_text="Produit"
    )

    # Date de la prévision
    forecast_date = models.DateField(
        help_text="Date pour laquelle on prédit (ex: 2026-07-01)"
    )

    # Quantité prédite
    predicted_quantity = models.PositiveIntegerField(
        help_text="Nombre d'unités prédites pour cette date"
    )

    # Confiance du modèle
    confidence_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.0,
        help_text="Confiance du modèle (0.0 à 1.0)",
    )

    # Date de création
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Date du calcul de la prévision"
    )

    class Meta:
        verbose_name = _("Forecast")
        verbose_name_plural = _("Forecasts")
        ordering = ["-forecast_date"]

    def __str__(self):
        return f"Prévision {self.product.name} ({self.forecast_date})"


class Alert(models.Model):
    """
    Alerte basée sur une prévision.

    Si la prévision dit "150 unités vendues"
    et le stock actuel est "30 unités",
    on génère une alerte CRITICAL.

    Sevérités :
    - low : Stock suffisant (95%+)
    - medium : Stock moyen (50-95%)
    - high : Stock bas (10-50%)
    - critical : Stock très bas (< 10%)

    Champs :
    - product : Produit
    - forecast : Prévision associée
    - message : Description de l'alerte
    - severity : Niveau de sévérité
    - created_at : Date
    """

    SEVERITY_CHOICES = [
        ("low", _("Low")),
        ("medium", _("Medium")),
        ("high", _("High")),
        ("critical", _("Critical")),
    ]

    # Identifiant
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Produit
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="alerts", help_text="Produit"
    )

    # Prévision
    forecast = models.ForeignKey(
        Forecast,
        on_delete=models.CASCADE,
        related_name="alerts",
        help_text="Prévision associée",
    )

    # Message
    message = models.TextField(help_text="Description de l'alerte")

    # Sévérité
    severity = models.CharField(
        max_length=20, choices=SEVERITY_CHOICES, help_text="Niveau de sévérité"
    )

    # Date
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Alert")
        verbose_name_plural = _("Alerts")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Alerte {self.product.name} - {self.severity}"
