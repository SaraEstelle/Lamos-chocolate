"""
apps/customer_area/models.py
============================
Customer area models.

CustomerAddress: a saved shipping address. A customer can have several
addresses and mark one as default (used to pre-fill checkout).
"""

import uuid

from django.db import models

from apps.common.constants import SwissCantonChoices


class CustomerAddress(models.Model):
    """A saved shipping address belonging to a customer."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        "accounts.Customer",
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    label = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Friendly name, e.g. 'Home' or 'Office'",
    )
    full_name = models.CharField(max_length=200)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    canton = models.CharField(
        max_length=2,
        choices=SwissCantonChoices.choices,
        blank=True,
        default="",
        help_text="Swiss canton, used for the sales heatmap.",
    )
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "customer_addresses"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.label or self.city} —{self.customer.email}"

    def save(self, *args, **kwargs):
        """Ensure only one default address per customer and keep the
        customer's denormalized canton/npa in sync with the default address."""
        if self.is_default:
            # Unset other defaults for this customer
            CustomerAddress.objects.filter(
                customer=self.customer, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

        # Denormalize canton + npa onto the customer for fast heatmap KPIs.
        # Resolve the model from the FK (self.customer may be a lazy request.user).
        if self.is_default:
            customer_model = self._meta.get_field("customer").related_model
            customer_model.objects.filter(pk=self.customer_id).update(
                canton=self.canton,
                npa=self.postal_code,
            )
