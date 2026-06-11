"""
apps/checkout/models.py
=======================
Modèles de commandes et paiements (Stripe).

Modèles :
1. Order — Commande d'un client
2. OrderItem — Produit dans la commande
3. Payment — Paiement Stripe associé à la commande

Relations :
Customer → Order (1 client peut avoir plusieurs commandes)
Order → OrderItem (1 commande contient plusieurs articles)
Order → Payment (1 commande = 1 paiement)
OrderItem → Product (lien vers le produit)

Cycle de vie d'une commande :
1. pending → Cliente a soumis, Stripe en cours
2. paid → Paiement réussi (Payment.succeeded)
3. shipped → Commande expédiée
4. delivered → Livrée
5. cancelled → Annulée

Règulation Suisse (RGPD) :
- Pas de stockage des numéros de carte (Stripe s'en charge)
- Chiffrement du numero de commande
- Archivage 10 ans pour comptabilité
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import Customer
from apps.shop.models import Product


class Order(models.Model):
    """
    Commande d'un client.

    Statuts :
    - pending : En attente de paiement
    - paid : Paiement reçu
    - shipped : Expédiée
    - delivered : Livrée
    - cancelled : Annulée

    Champs :
    - customer : Client
    - order_number : Numéro de commande (unique, pour invoice)
    - status : Statut de la commande
    - total_amount : Prix total
    - shipping_address : Adresse de livraison
    - billing_address : Adresse de facturation
    - created_at, updated_at : Dates
    """

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('paid', _('Paid')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
    ]

    # Identifiant
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Client
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,  # Ne pas supprimer les commandes si client supprimé
        related_name='orders',
        help_text="Client qui a fait la commande"
    )

    # Numéro de commande (pour facture)
    order_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Numéro unique de commande (ex: CMD-2024-0001)"
    )

    # Statut
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Statut de la commande"
    )

    # Prix total
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Prix total en CHF"
    )

    # Adresses
    shipping_address = models.TextField(
        help_text="Adresse de livraison"
    )

    billing_address = models.TextField(
        help_text="Adresse de facturation"
    )

    # Dates
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ['-created_at']

    def __str__(self):
        return f"Commande {self.order_number}"


class OrderItem(models.Model):
    """
    Produit dans une commande.

    Exemple :
    - Order = CMD-2024-0001
    - OrderItem 1 = Chocolat noir 70%, quantité 2, prix 12.50 CHF chacun
    - OrderItem 2 = Truffe noisette, quantité 1, prix 8.00 CHF

    Note : on garde une copie du prix (unit_price)
    car le prix du produit peut changer après la commande.
    """

    # Identifiant
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Commande
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="Commande"
    )

    # Produit
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        help_text="Produit commandé"
    )

    # Quantité
    quantity = models.PositiveIntegerField(
        help_text="Nombre d'unités commandées"
    )

    # Prix unitaire au moment de la commande
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Prix unitaire au moment de la commande"
    )

    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    def get_subtotal(self):
        """Calculer le prix total de cet article"""
        return self.unit_price * self.quantity


class Payment(models.Model):
    """
    Paiement Stripe.

    Chaque commande a exactement 1 paiement.
    Le paiement peut avoir plusieurs statuts :
    - pending : En attente
    - succeeded : Réussi (argent reçu)
    - failed : Échoué (carte refusée, etc.)
    - refunded : Remboursé

    Champs :
    - order : Commande associée
    - stripe_payment_intent : ID Stripe pour traçabilité
    - amount : Montant
    - status : Statut
    - paid_at : Date du paiement

    Sécurité :
    - Vérifier TOUJOURS la signature Stripe dans le webhook
    - Ne JAMAIS faire confiance au client sur le montant
    - Stocker l'ID Stripe pour traçabilité et remboursement
    """

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('succeeded', _('Succeeded')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    ]

    # Identifiant
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Commande
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment',
        help_text="Commande payée"
    )

    # Références Stripe
    stripe_payment_intent = models.CharField(
        max_length=255,
        unique=True,
        help_text="ID PaymentIntent de Stripe"
    )

    # Montant
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Montant en CHF"
    )

    # Statut
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Statut du paiement"
    )

    # Date de paiement
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date du paiement réussi"
    )

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")

    def __str__(self):
        return f"Paiement {self.order.order_number} - {self.status}"