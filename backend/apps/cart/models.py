"""
apps/cart/models.py
===================
Modèles du panier (shopping cart).

Modèles :
1. Cart — Panier d'un client
2. CartItem — Produit dans le panier

Relations :
Customer → Cart (1 client = 1 panier actif)
Cart → CartItem (1 panier peut contenir plusieurs articles)
CartItem → Product (lien vers le produit)

Note :
Le panier est stocké en DB (pas en session).
Avantage : persist across sessions, synchronisation multiple devices.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import Customer
from apps.shop.models import Product


class Cart(models.Model):
    """
    Panier d'un client.

    Chaque client a un panier actif (session).
    Quand il checkout, le panier est converti en Order.

    Champs :
    - customer : Client propriétaire
    - created_at : Date de création
    - updated_at : Date de modification
    """

    # Identifiant
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Client propriétaire
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='carts',
        help_text="Client propriétaire du panier"
    )

    # Dates
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = _("Cart")
        verbose_name_plural = _("Carts")
        ordering = ['-updated_at']

    def __str__(self):
        return f"Panier de {self.customer.email}"

    def get_total_price(self):
        """Calculer le prix total du panier"""
        return sum(
            item.product.price * item.quantity
            for item in self.items.all()
        )

    def get_total_items(self):
        """Calculer le nombre total d'articles"""
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """
    Article dans le panier.

    Exemple :
    - Panier = 1
    - CartItem 1 = Chocolat noir 70%, quantité 2
    - CartItem 2 = Truffe noisette, quantité 1

    Champs :
    - cart : Panier
    - product : Produit
    - quantity : Nombre d'unités
    """

    # Identifiant
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Panier
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="Panier auquel appartient cet article"
    )

    # Produit
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        help_text="Produit"
    )

    # Quantité
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="Nombre d'unités du produit"
    )

    class Meta:
        verbose_name = _("Cart Item")
        verbose_name_plural = _("Cart Items")
        unique_together = ('cart', 'product')  # 1 produit maximum par panier

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    def get_subtotal(self):
        """Calculer le prix de cet article"""
        return self.product.price * self.quantity