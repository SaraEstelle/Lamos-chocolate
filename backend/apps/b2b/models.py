"""
apps/b2b/models.py
==================
Modèles B2B (partenariats professionnels).

Modèle :
1. BusinessRequest — Demande de partenariat B2B

Qu'est-ce que B2B ?
B2B = Business to Business = entreprise à entreprise
Exemples de clients B2B :
- Restaurants (pour vendre du chocolat)
- Hotels (pour chambres d'hôtes)
- Entreprises (pour cadeau d'affaires)
- Magasins (pour revente)

Cycle de vie d'une demande B2B :
1. pending → Reçue, à revue manuelle
2. reviewed → Révue par un admin
3. approved → Acceptée, contact en cours
4. rejected → Refusée (pas intéressé)

Règulation Suisse (RGPD) :
- Consentement explicite pour marketing
- Droit d'opposition
- Durée de conservation = 3 ans max
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import Customer


class BusinessRequest(models.Model):
    """
    Demande de partenariat B2B.

    Quand une entreprise remplit le formulaire B2B :
    /b2b/request-form

    Un BusinessRequest est créé.
    Un admin le révise et accepte/refuse.

    Champs :
    - customer : Client qui demande (peut être null si anonyme)
    - company_name : Nom de l'entreprise
    - contact_name : Personne de contact
    - email : Email de contact
    - phone : Téléphone
    - message : Détails de la demande
    - status : État (pending, reviewed, approved, rejected)
    - created_at : Date de création
    """

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('reviewed', _('Reviewed')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    # Identifiant
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Client (optionnel, peut être anonyme)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='b2b_requests',
        help_text="Client (optionnel, peut être anonyme)"
    )

    # Entreprise
    company_name = models.CharField(
        max_length=255,
        help_text="Nom de l'entreprise"
    )

    # Personne de contact
    contact_name = models.CharField(
        max_length=255,
        help_text="Nom du responsable"
    )

    # Email
    email = models.EmailField(
        help_text="Email de contact"
    )

    # Téléphone
    phone = models.CharField(
        max_length=20,
        help_text="Numéro de téléphone"
    )

    # Message
    message = models.TextField(
        help_text="Détails de la demande de partenariat"
    )

    # Statut
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="État de la demande"
    )

    # Dates
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = _("Business Request")
        verbose_name_plural = _("Business Requests")
        ordering = ['-created_at']

    def __str__(self):
        return f"Demande B2B - {self.company_name}"