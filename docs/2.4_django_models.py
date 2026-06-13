"""
LAMOS CHOCOLATE — Django ORM Models
Section 2.4 of Technical Documentation (Stage 3)
Stack: Django 5.x · PostgreSQL 16
"""

from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
import math
import secrets
import string
from datetime import timedelta


# ----------------------------------------------------------------
# ENUM-LIKE CHOICES (mapped to PostgreSQL ENUM via migration)
# ----------------------------------------------------------------

class CurrencyChoices(models.TextChoices):
    EUR = 'EUR', 'Euro'
    CHF = 'CHF', 'Franc suisse'


class LanguageChoices(models.TextChoices):
    FR = 'fr', 'Français'
    EN = 'en', 'English'


class OrderStatusChoices(models.TextChoices):
    PENDING    = 'pending', 'En attente'
    PAID       = 'paid', 'Payé'
    PROCESSING = 'processing', 'En préparation'
    SHIPPED    = 'shipped', 'Expédié'
    DELIVERED  = 'delivered', 'Livré'
    CANCELLED  = 'cancelled', 'Annulé'
    REFUNDED   = 'refunded', 'Remboursé'


class B2BStatusChoices(models.TextChoices):
    NEW         = 'new', 'Nouvelle'
    IN_PROGRESS = 'in_progress', 'En cours'
    CONVERTED   = 'converted', 'Convertie'
    REFUSED     = 'refused', 'Refusée'


class AdminRoleChoices(models.TextChoices):
    SUPERADMIN = 'superadmin', 'Super administrateur'
    ADMIN      = 'admin', 'Administrateur'
    VIEWER     = 'viewer', 'Lecteur'


# ----------------------------------------------------------------
# MODEL : Category
# ----------------------------------------------------------------

class Category(models.Model):
    name_fr    = models.CharField(max_length=100)
    name_en    = models.CharField(max_length=100)
    slug       = models.SlugField(max_length=120, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'categories'
        ordering = ['name_fr']

    def __str__(self):
        return self.name_fr

    def get_name(self, lang='fr'):
        return self.name_en if lang == 'en' else self.name_fr


# ----------------------------------------------------------------
# MODEL : Product
# ----------------------------------------------------------------

class Product(models.Model):
    slug           = models.SlugField(max_length=160, unique=True)
    name_fr        = models.CharField(max_length=200)
    name_en        = models.CharField(max_length=200)
    description_fr = models.TextField(blank=True, default='')
    description_en = models.TextField(blank=True, default='')
    ingredients_fr = models.TextField(blank=True, default='')
    ingredients_en = models.TextField(blank=True, default='')
    allergens_fr   = models.CharField(max_length=500, blank=True, default='')
    allergens_en   = models.CharField(max_length=500, blank=True, default='')
    category       = models.ForeignKey(
        Category,
        on_delete=models.RESTRICT,
        related_name='products'
    )
    image_url      = models.CharField(max_length=500, blank=True, default='')
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
        ]

    def __str__(self):
        return self.name_fr

    def get_name(self, lang='fr'):
        return self.name_en if lang == 'en' else self.name_fr

    def get_description(self, lang='fr'):
        return self.description_en if lang == 'en' else self.description_fr

    def get_allergens(self, lang='fr'):
        return self.allergens_en if lang == 'en' else self.allergens_fr


# ----------------------------------------------------------------
# MODEL : SKU (Stock Keeping Unit)
# Includes forecasting columns: production_delay_days, batch_size
# ----------------------------------------------------------------

class SKU(models.Model):
    product              = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='skus'
    )
    sku_code             = models.CharField(max_length=60, unique=True)
    format               = models.CharField(max_length=100)
    weight_g             = models.PositiveIntegerField(null=True, blank=True)
    price                = models.DecimalField(max_digits=10, decimal_places=2)
    currency             = models.CharField(
        max_length=3,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.EUR
    )
    is_active            = models.BooleanField(default=True)
    production_delay_days = models.PositiveIntegerField(default=7)
    batch_size           = models.PositiveIntegerField(default=50)
    created_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'skus'
        verbose_name = 'SKU'
        verbose_name_plural = 'SKUs'

    def __str__(self):
        return f"{self.sku_code} — {self.product.name_fr} ({self.format})"

    def calculate_estimated_days(self, order_quantity, shipping_zone):
        """
        Forecasting model — estimated delivery time.

        Case 1: stock >= order_quantity → shipping delay only
        Case 2: stock < order_quantity → production + shipping
        Case 3: stock == 0 → full production + shipping
        """
        stock = self.stock
        available = stock.quantity

        if available >= order_quantity:
            return shipping_zone.delay_days

        deficit = order_quantity - available
        batches_needed = math.ceil(deficit / self.batch_size)
        production_days = batches_needed * self.production_delay_days

        return production_days + shipping_zone.delay_days


# ----------------------------------------------------------------
# MODEL : Stock
# ----------------------------------------------------------------

class Stock(models.Model):
    sku             = models.OneToOneField(
        SKU,
        on_delete=models.CASCADE,
        related_name='stock'
    )
    quantity        = models.PositiveIntegerField(default=0)
    threshold_alert = models.PositiveIntegerField(default=5)
    updated_at      = models.DateTimeField(auto_now=True)
    updated_by      = models.ForeignKey(
        'AdminUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'stock'

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
        self.save(update_fields=['quantity', 'updated_at'])

    def increment(self, qty):
        self.quantity += qty
        self.save(update_fields=['quantity', 'updated_at'])


# ----------------------------------------------------------------
# MODEL : ShippingZone (Forecasting)
# ----------------------------------------------------------------

class ShippingZone(models.Model):
    zone_name  = models.CharField(max_length=100)
    countries  = ArrayField(
        models.CharField(max_length=3),
        help_text="ISO 3166-1 alpha-2 country codes"
    )
    delay_days = models.PositiveIntegerField(default=5)
    cost       = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'shipping_zones'

    def __str__(self):
        return f"{self.zone_name} ({self.delay_days}d)"

    @classmethod
    def get_zone_for_country(cls, country_code):
        return cls.objects.filter(countries__contains=[country_code]).first()


# ----------------------------------------------------------------
# MODEL : Customer
# ----------------------------------------------------------------

class Customer(models.Model):
    first_name    = models.CharField(max_length=100)
    last_name     = models.CharField(max_length=100)
    email         = models.EmailField(max_length=255, unique=True)
    password_hash = models.CharField(max_length=255)
    phone         = models.CharField(max_length=30, blank=True, default='')
    address_line1 = models.CharField(max_length=255, blank=True, default='')
    address_line2 = models.CharField(max_length=255, blank=True, default='')
    city          = models.CharField(max_length=100, blank=True, default='')
    postal_code   = models.CharField(max_length=20, blank=True, default='')
    country       = models.CharField(max_length=100, blank=True, default='')
    language_pref = models.CharField(
        max_length=2,
        choices=LanguageChoices.choices,
        default=LanguageChoices.FR
    )
    is_active     = models.BooleanField(default=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    last_login    = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'customers'
        indexes = [
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


# ----------------------------------------------------------------
# MODEL : Order
# ----------------------------------------------------------------

class Order(models.Model):
    customer             = models.ForeignKey(
        Customer,
        on_delete=models.RESTRICT,
        related_name='orders'
    )
    order_number         = models.CharField(max_length=30, unique=True)
    status               = models.CharField(
        max_length=20,
        choices=OrderStatusChoices.choices,
        default=OrderStatusChoices.PENDING
    )
    total_amount         = models.DecimalField(max_digits=10, decimal_places=2)
    currency             = models.CharField(
        max_length=3,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.EUR
    )
    stripe_payment_id    = models.CharField(max_length=255, blank=True, default='')
    stripe_session_id    = models.CharField(max_length=255, blank=True, default='')
    shipping_first_name  = models.CharField(max_length=100, blank=True, default='')
    shipping_last_name   = models.CharField(max_length=100, blank=True, default='')
    shipping_address1    = models.CharField(max_length=255, blank=True, default='')
    shipping_address2    = models.CharField(max_length=255, blank=True, default='')
    shipping_city        = models.CharField(max_length=100, blank=True, default='')
    shipping_postal_code = models.CharField(max_length=20, blank=True, default='')
    shipping_country     = models.CharField(max_length=100, blank=True, default='')
    language             = models.CharField(
        max_length=2,
        choices=LanguageChoices.choices,
        default=LanguageChoices.FR
    )
    notes                    = models.TextField(blank=True, default='')
    estimated_delivery_days  = models.PositiveIntegerField(null=True, blank=True)
    created_at               = models.DateTimeField(auto_now_add=True)
    updated_at               = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['customer']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Order {self.order_number} — {self.status}"

    @staticmethod
    def generate_order_number():
        date_part = timezone.now().strftime('%Y%m%d')
        random_part = ''.join(
            secrets.choice(string.ascii_uppercase + string.digits)
            for _ in range(5)
        )
        return f"LM-{date_part}-{random_part}"


# ----------------------------------------------------------------
# MODEL : OrderItem
# ----------------------------------------------------------------

class OrderItem(models.Model):
    order      = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    sku        = models.ForeignKey(
        SKU,
        on_delete=models.RESTRICT,
        related_name='order_items'
    )
    quantity   = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal   = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_items'

    def __str__(self):
        return f"{self.quantity}x {self.sku.sku_code} @ {self.unit_price}"

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# ----------------------------------------------------------------
# MODEL : AdminUser
# ----------------------------------------------------------------

class AdminUser(models.Model):
    email         = models.EmailField(max_length=255, unique=True)
    password_hash = models.CharField(max_length=255)
    first_name    = models.CharField(max_length=100, blank=True, default='')
    last_name     = models.CharField(max_length=100, blank=True, default='')
    role          = models.CharField(
        max_length=20,
        choices=AdminRoleChoices.choices,
        default=AdminRoleChoices.ADMIN
    )
    is_active     = models.BooleanField(default=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    last_login    = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'admin_users'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)


# ----------------------------------------------------------------
# MODEL : B2BRequest
# ----------------------------------------------------------------

class B2BRequest(models.Model):
    company_name  = models.CharField(max_length=200)
    contact_name  = models.CharField(max_length=200)
    contact_email = models.EmailField(max_length=255)
    contact_phone = models.CharField(max_length=30, blank=True, default='')
    sector        = models.CharField(max_length=100, blank=True, default='')
    estimated_qty = models.PositiveIntegerField(null=True, blank=True)
    occasion      = models.CharField(max_length=200, blank=True, default='')
    message       = models.TextField(blank=True, default='')
    status        = models.CharField(
        max_length=20,
        choices=B2BStatusChoices.choices,
        default=B2BStatusChoices.NEW
    )
    language      = models.CharField(
        max_length=2,
        choices=LanguageChoices.choices,
        default=LanguageChoices.FR
    )
    ip_address    = models.GenericIPAddressField(null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    processed_at  = models.DateTimeField(null=True, blank=True)
    processed_by  = models.ForeignKey(
        AdminUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'b2b_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"B2B — {self.company_name} ({self.status})"


# ----------------------------------------------------------------
# MODEL : PasswordResetToken
# ----------------------------------------------------------------

class PasswordResetToken(models.Model):
    customer   = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='reset_tokens'
    )
    token      = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    used       = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'password_reset_tokens'
        indexes = [
            models.Index(
                fields=['token'],
                condition=models.Q(used=False),
                name='idx_reset_tokens_valid'
            ),
        ]

    def __str__(self):
        return f"Reset token for {self.customer.email}"

    @property
    def is_valid(self):
        return not self.used and self.expires_at > timezone.now()

    @classmethod
    def create_for_customer(cls, customer):
        token = secrets.token_urlsafe(48)
        return cls.objects.create(
            customer=customer,
            token=token,
            expires_at=timezone.now() + timedelta(hours=1)
        )
