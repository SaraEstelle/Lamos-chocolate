"""
apps/cockpit/models.py
======================
Persistent state for the executive cockpit. Until the Pilotage tab, the
cockpit was read-only (selectors over Order/OrderItem). These models hold the
*objectives* the Direction sets from the Pilotage tab, which then feed the
Pulse gauges and the actual-vs-target comparisons.
"""

from django.conf import settings
from django.db import models

from apps.common.constants import SwissCantonChoices
from apps.shop.models import Product


class CockpitObjective(models.Model):
    """Company-wide executive targets (single row, pk=1).

    Replaces the hardcoded placeholder constants that used to live in
    selectors.py (PRD §12 #4 — objectif CA jour/mois + capacité usine).
    """

    daily_revenue_chf = models.PositiveIntegerField(default=3000)
    monthly_revenue_chf = models.PositiveIntegerField(default=80000)
    monthly_capacity_units = models.PositiveIntegerField(default=50000)
    target_margin_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=40,
        help_text="Target gross margin, in percent.",
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        verbose_name = "Objectif cockpit"
        verbose_name_plural = "Objectifs cockpit"

    def __str__(self):
        return "Objectifs Direction"

    def save(self, *args, **kwargs):
        # Enforce the singleton: there is only ever one objectives row.
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Return the single objectives row, creating it with defaults if needed."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ProductTarget(models.Model):
    """Per-product monthly sales objective, in units."""

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="cockpit_target",
    )
    monthly_units = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Objectif produit"
        verbose_name_plural = "Objectifs produits"

    def __str__(self):
        return f"{self.product.name_fr} → {self.monthly_units} u/mois"


class CantonTarget(models.Model):
    """Per-canton monthly revenue objective, in CHF (drives the heatmap goals)."""

    canton = models.CharField(
        max_length=2,
        choices=SwissCantonChoices.choices,
        unique=True,
    )
    monthly_revenue_chf = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Objectif canton"
        verbose_name_plural = "Objectifs cantons"

    def __str__(self):
        return f"{self.canton} → {self.monthly_revenue_chf} CHF/mois"
