"""
apps/shop/models.py
===================
Modèles du catalogue de produits.

Modèles :
1. Category — Catégorie de produits (Chocolats noirs, au lait, remplis, etc.)
2. Product — Produit vendable (une barre de chocolat)
3. ProductImage — Images du produit (jusqu'à 10 images par produit)
4. Stock — Gestion des stocks (quantité disponible, alerte bas de stock)

Relations :
Category → Product (1 catégorie peut avoir plusieurs produits)
Product → ProductImage (1 produit peut avoir plusieurs images)
Product → Stock (1 produit a exactement 1 stock)

Règulation Suisse (RGPD) :
- Traçabilité du stock (updated_at)
- Informations sur l'allergie et la composition
"""

import uuid
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """
    Catégorie de produits.

    Exemples :
    - Chocolats noirs
    - Chocolats au lait
    - Chocolats remplis
    - Truffes
    - Barres protéinées

    Champs :
    - name : Nom de la catégorie
    - slug : URL-friendly version du nom (unique, pour les URLs)
    - description : Description longue
    """

    # Identifiant
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Nom de la catégorie
    name = models.CharField(
        max_length=255,
        help_text="Nom de la catégorie (ex: Chocolats noirs)"
    )

    # Slug pour URLs (/shop/category/chocolats-noirs/)
    slug = models.SlugField(
        unique=True,
        help_text="URL-friendly version du nom (auto-generated)"
    )

    # Description longue
    description = models.TextField(
        blank=True,
        help_text="Description détaillée de la catégorie"
    )

    # Dates
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Avant de sauvegarder, générer le slug à partir du nom.
        Cela permet au développeur de ne pas le taper.
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Produit vendable.

    Exemples :
    - Tablette de chocolat noir 70%
    - Truffe aux noisettes
    - Assortiment de 12 truffes

    Champs :
    - category : Catégorie
    - name : Nom du produit
    - slug : URL-friendly
    - short_description : Description courte (pour listing)
    - description : Description longue (pour détail)
    - price : Prix en CHF
    - weight : Poids en grammes
    - is_active : Publié ou non
    """

    # Identifiant
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Catégorie
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,  # Ne pas supprimer la catégorie si des produits l'utilisent
        related_name='products',
        help_text="Catégorie du produit"
    )

    # Nom
    name = models.CharField(
        max_length=255,
        help_text="Nom du produit"
    )

    # Slug pour URLs
    slug = models.SlugField(
        unique=True,
        help_text="URL-friendly version du nom"
    )

    # Descriptions
    short_description = models.TextField(
        help_text="Description courte (pour listing produits)"
    )

    description = models.TextField(
        help_text="Description longue (pour détail produit)"
    )

    # Prix en CHF (francs suisses)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Prix en CHF (ex: 12.50)"
    )

    # Poids en grammes
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=100,
        help_text="Poids en grammes (ex: 100)"
    )

    # Statut de publication
    is_active = models.BooleanField(
        default=True,
        help_text="Publié sur le site ? (False = caché)"
    )

    # Dates
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Générer le slug à partir du nom"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    """
    Image d'un produit.

    Un produit peut avoir plusieurs images :
    - Image 1 : vue de face
    - Image 2 : vue de côté
    - Image 3 : détail du packaging
    - Image 4 : contenu intérieur
    - etc.

    Une image peut être marquée comme "principale"
    (celle affichée sur le listing).

    Champs :
    - product : Produit
    - image : Fichier image (JPEG, PNG)
    - alt_text : Texte alternatif (pour accessibilité SEO)
    - is_primary : Image principale ?
    """

    # Identifiant
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Produit
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,  # Supprimer l'image si le produit est supprimé
        related_name='images',
        help_text="Produit auquel appartient cette image"
    )

    # Fichier image
    image = models.ImageField(
        upload_to='products/',  # Dossier media/products/
        help_text="Fichier image (JPEG, PNG)"
    )

    # Texte alternatif
    alt_text = models.CharField(
        max_length=255,
        help_text="Description de l'image (pour SEO et accessibilité)"
    )

    # Image principale ?
    is_primary = models.BooleanField(
        default=False,
        help_text="Cette image est-elle la principale ?"
    )

    class Meta:
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")
        ordering = ['-is_primary', 'id']

    def __str__(self):
        return f"Image de {self.product.name}"


class Stock(models.Model):
    """
    Gestion des stocks.

    Suivi de la quantité disponible pour chaque produit.
    Alerte automatique si quantité < minimum_threshold.

    Exemple :
    - quantity = 150 (150 unités en stock)
    - minimum_threshold = 20 (alerte si < 20)

    Champs :
    - product : Produit (OneToOneField = 1 produit = 1 stock)
    - quantity : Quantité actuelle
    - minimum_threshold : Seuil d'alerte
    - updated_at : Dernière modification
    """

    # Identifiant
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Produit (1 produit = 1 stock, pas plusieurs)
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='stock',
        help_text="Produit"
    )

    # Quantité actuelle
    quantity = models.PositiveIntegerField(
        default=0,
        help_text="Nombre d'unités disponibles"
    )

    # Seuil d'alerte
    minimum_threshold = models.PositiveIntegerField(
        default=10,
        help_text="Alerte si quantité < ce nombre"
    )

    # Dernière modification
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Dernière modification du stock"
    )

    class Meta:
        verbose_name = _("Stock")
        verbose_name_plural = _("Stocks")

    def __str__(self):
        return f"Stock de {self.product.name} ({self.quantity} units)"

    def is_low(self):
        """Vérifier si le stock est bas"""
        return self.quantity < self.minimum_threshold