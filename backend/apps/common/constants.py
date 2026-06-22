"""Shared enum-like choices used across apps (mapped from PostgreSQL ENUMs)."""

from django.db import models


class CurrencyChoices(models.TextChoices):
    EUR = "EUR", "Euro"
    CHF = "CHF", "Franc suisse"


class LanguageChoices(models.TextChoices):
    FR = "fr", "Français"
    EN = "en", "English"


class OrderStatusChoices(models.TextChoices):
    PENDING = "pending", "En attente"
    PAID = "paid", "Payé"
    PROCESSING = "processing", "En préparation"
    SHIPPED = "shipped", "Expédié"
    DELIVERED = "delivered", "Livré"
    CANCELLED = "cancelled", "Annulé"
    REFUNDED = "refunded", "Remboursé"


class B2BStatusChoices(models.TextChoices):
    NEW = "new", "Nouvelle"
    IN_PROGRESS = "in_progress", "En cours"
    CONVERTED = "converted", "Convertie"
    REFUSED = "refused", "Refusée"


class AdminRoleChoices(models.TextChoices):
    SUPERADMIN = "superadmin", "Super administrateur"
    ADMIN = "admin", "Administrateur"
    VIEWER = "viewer", "Lecteur"


class PaymentStatusChoices(models.TextChoices):
    PENDING = "pending", "En attente"
    SUCCEEDED = "succeeded", "Réussi"
    FAILED = "failed", "Échoué"
    REFUNDED = "refunded", "Remboursé"


class CustomerTypeChoices(models.TextChoices):
    """Customer segmentation used across KPIs and the executive cockpit."""
    B2C = "b2c", "Particulier (B2C)"
    B2B_DISTRIBUTOR = "b2b_distributor", "Distributeur (B2B)"
    B2B_HOSPITALITY = "b2b_hospitality", "Hôtel / Corporate (B2B)"


class ChannelChoices(models.TextChoices):
    """Sales channel for an order (used to split cockpit views)."""
    B2C = "b2c", "B2C"
    B2B = "b2b", "B2B"


class SwissCantonChoices(models.TextChoices):
    """Swiss cantons (for the sales heatmap)."""
    VD = "VD", "Vaud"
    GE = "GE", "Genève"
    ZH = "ZH", "Zürich"
    BE = "BE", "Bern"
    VS = "VS", "Valais"
    FR = "FR", "Fribourg"
    NE = "NE", "Neuchâtel"
    JU = "JU", "Jura"
    TI = "TI", "Ticino"
    # Add the remaining cantons later (26 total). For the demo these + OTHER suffice.
    OTHER = "XX", "Autre / Hors Suisse"


class B2BSegmentChoices(models.TextChoices):
    """B2B account segment."""
    DISTRIBUTOR = "distributor", "Distributeur"
    HOTEL = "hotel", "Hôtel"
    CORPORATE = "corporate", "Corporate"


class B2BAccountStatusChoices(models.TextChoices):
    """Lifecycle status of a B2B account."""
    PROSPECT = "prospect", "Prospect"
    ACTIVE = "active", "Actif"
    DORMANT = "dormant", "Dormant"