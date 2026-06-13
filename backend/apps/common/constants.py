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
