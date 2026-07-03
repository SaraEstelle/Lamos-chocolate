import secrets
import string
import uuid

from django.db import models
from django.utils import timezone

from apps.common.constants import (
    ChannelChoices,
    CurrencyChoices,
    LanguageChoices,
    OrderStatusChoices,
    PaymentStatusChoices,
)


class Order(models.Model):
    customer = models.ForeignKey(
        "accounts.Customer",
        on_delete=models.RESTRICT,
        related_name="orders",
    )
    shipping_zone = models.ForeignKey(
        "shop.ShippingZone",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="Delivery zone applied at order time (forecasting).",
    )
    order_number = models.CharField(max_length=30, unique=True)
    status = models.CharField(
        max_length=20,
        choices=OrderStatusChoices.choices,
        default=OrderStatusChoices.PENDING,
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.EUR,
    )
    stripe_session_id = models.CharField(max_length=255, blank=True, default="")
    shipping_first_name = models.CharField(max_length=100, blank=True, default="")
    shipping_last_name = models.CharField(max_length=100, blank=True, default="")
    shipping_address1 = models.CharField(max_length=255, blank=True, default="")
    shipping_address2 = models.CharField(max_length=255, blank=True, default="")
    shipping_city = models.CharField(max_length=100, blank=True, default="")
    shipping_postal_code = models.CharField(max_length=20, blank=True, default="")
    shipping_country = models.CharField(max_length=100, blank=True, default="")
    language = models.CharField(
        max_length=2,
        choices=LanguageChoices.choices,
        default=LanguageChoices.FR,
    )
    notes = models.TextField(blank=True, default="")
    estimated_delivery_days = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    channel = models.CharField(
        max_length=3,
        choices=ChannelChoices.choices,
        default=ChannelChoices.B2C,
        help_text="Sales channel (b2c/b2b) for cockpit splitting",
    )
    campaign_period = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Seasonal campaign (e.g. Noel, Saint-Valentin) for seasonality KPI",
    )

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["customer"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"Order {self.order_number} — {self.status}"

    @staticmethod
    def generate_order_number():
        date_part = timezone.now().strftime("%Y%m%d")
        random_part = "".join(
            secrets.choice(string.ascii_uppercase + string.digits) for _ in range(5)
        )
        return f"LM-{date_part}-{random_part}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    sku = models.ForeignKey(
        "shop.SKU",
        on_delete=models.RESTRICT,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "order_items"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="order_items_quantity_gt_0",
            ),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.sku.sku_code} @ {self.unit_price}"

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="payment",
    )
    stripe_payment_intent = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.EUR,
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatusChoices.choices,
        default=PaymentStatusChoices.PENDING,
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"

    def __str__(self):
        return f"Payment {self.order.order_number} — {self.status}"
