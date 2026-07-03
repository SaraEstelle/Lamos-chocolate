import math
import uuid
from decimal import Decimal

from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.common.constants import CurrencyChoices


class Category(models.Model):
    name_fr = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "categories"
        verbose_name_plural = "categories"
        ordering = ["name_fr"]

    def __str__(self):
        return self.name_fr

    def get_name(self, lang="fr"):
        return self.name_en if lang == "en" else self.name_fr


class Product(models.Model):
    slug = models.SlugField(max_length=160, unique=True)
    name_fr = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    description_fr = models.TextField(blank=True, default="")
    description_en = models.TextField(blank=True, default="")
    ingredients_fr = models.TextField(blank=True, default="")
    ingredients_en = models.TextField(blank=True, default="")
    allergens_fr = models.CharField(max_length=500, blank=True, default="")
    allergens_en = models.CharField(max_length=500, blank=True, default="")
    category = models.ForeignKey(
        Category,
        on_delete=models.RESTRICT,
        related_name="products",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "-created_at"]),
        ]

    def __str__(self):
        return self.name_fr

    def get_name(self, lang="fr"):
        return self.name_en if lang == "en" else self.name_fr

    def get_description(self, lang="fr"):
        return self.description_en if lang == "en" else self.description_fr

    def get_allergens(self, lang="fr"):
        return self.allergens_en if lang == "en" else self.allergens_fr

    @property
    def primary_image_url(self):
        """URL of the primary image, else the first one, else an empty string."""
        image = self.images.filter(is_primary=True).first() or self.images.first()
        return image.image_url if image else ""


class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image_url = models.CharField(max_length=500)
    alt_text = models.CharField(max_length=255, blank=True, default="")
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_images"
        ordering = ["-is_primary", "created_at"]

    def __str__(self):
        return f"Image of {self.product.name_fr}"


class SKU(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="skus",
    )
    sku_code = models.CharField(max_length=60, unique=True)
    format = models.CharField(max_length=100)
    weight_g = models.PositiveIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.EUR,
    )
    is_active = models.BooleanField(default=True)
    production_delay_days = models.PositiveIntegerField(default=7)
    batch_size = models.PositiveIntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)

    cost_chf = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Production cost in CHF (for margin KPI)",
    )
    flavor = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Flavor variant (e.g. pistache, coffee, caramel)",
    )

    @property
    def margin(self):
        """Return the margin ratio (price - cost) / price, or None."""
        if self.cost_chf is None or self.price is None:
            return None

        price = Decimal(self.price)
        cost = Decimal(self.cost_chf)

        return float((price - cost) / price)

    class Meta:
        db_table = "skus"
        verbose_name = "SKU"
        verbose_name_plural = "SKUs"

    def __str__(self):
        return f"{self.sku_code} — {self.product.name_fr} ({self.format})"

    def calculate_estimated_days(self, order_quantity, shipping_zone):
        """Estimated delivery time (forecasting model).

        - stock >= order_quantity → shipping delay only
        - stock < order_quantity → production batches + shipping
        """
        available = self.stock.quantity

        if available >= order_quantity:
            return shipping_zone.delay_days

        deficit = order_quantity - available
        batches_needed = math.ceil(deficit / self.batch_size)
        production_days = batches_needed * self.production_delay_days

        return production_days + shipping_zone.delay_days


class Stock(models.Model):
    sku = models.OneToOneField(
        SKU,
        on_delete=models.CASCADE,
        related_name="stock",
    )
    quantity = models.PositiveIntegerField(default=0)
    threshold_alert = models.PositiveIntegerField(default=5)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.ForeignKey(
        "backoffice.AdminUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "stock"

    def __str__(self):
        return f"Stock {self.sku.sku_code}: {self.quantity}"

    @property
    def is_low(self):
        return self.quantity <= self.threshold_alert

    def decrement(self, qty):
        if self.quantity < qty:
            raise ValueError(
                f"Insufficient stock for {self.sku.sku_code}: "
                f"requested {qty}, available {self.quantity}"
            )
        self.quantity -= qty
        self.save(update_fields=["quantity", "updated_at"])

    def increment(self, qty):
        self.quantity += qty
        self.save(update_fields=["quantity", "updated_at"])


class ShippingZone(models.Model):
    zone_name = models.CharField(max_length=100)
    countries = ArrayField(
        models.CharField(max_length=3),
        help_text="ISO 3166-1 alpha-2 country codes",
    )
    delay_days = models.PositiveIntegerField(default=5)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "shipping_zones"

    def __str__(self):
        return f"{self.zone_name} ({self.delay_days}d)"

    @classmethod
    def get_zone_for_country(cls, country_code):
        return cls.objects.filter(countries__contains=[country_code]).first()
