"""
apps/customer_area/models.py
============================
Customer area models.

CustomerAddress: a saved shipping address. A customer can have several
addresses and mark one as default (used to pre-fill checkout).
"""

import uuid

from django.db import models


class CustomerAddress(models.Model):
    """A saved shipping address belonging to a customer."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        "accounts.Customer",
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    label = models.CharField(
        max_length=50, blank=True, default="",
        help_text="Friendly name, e.g. 'Home' or 'Office'",
    )
    full_name = models.CharField(max_length=200)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "customer_addresses"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.label or self.city} —{self.customer.email}"

    def save(self, *args, **kwargs):
        """Ensure only one default address per customer."""
        if self.is_default:
            # Unset other defaults for this customer
            CustomerAddress.objects.filter(
                customer=self.customer, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)