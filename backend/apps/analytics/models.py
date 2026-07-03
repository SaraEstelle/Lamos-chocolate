"""
apps/analytics/models.py
========================
Lightweight event tracking that feeds KPIs and the executive cockpit.

We store events in our own table (nLPD-friendly: no third party). The
`properties` JSON field keeps each event flexible while key dimensions
(channel, canton, campaign_period, value) are promoted to real columns so
they can be aggregated efficiently.
"""

import uuid

from django.db import models

from apps.common.constants import ChannelChoices


class EventTypeChoices(models.TextChoices):
    """Tracked event names (snake_case, per the data plan)."""

    PRODUCT_VIEW = "product_view", "Product view"
    ADD_TO_CART = "add_to_cart", "Add to cart"
    REMOVE_FROM_CART = "remove_from_cart", "Remove from cart"
    BEGIN_CHECKOUT = "begin_checkout", "Begin checkout"
    PURCHASE = "purchase", "Purchase"
    ACCOUNT_CREATED = "account_created", "Account created"
    LOGIN = "login", "Login"
    B2B_STOCK_VIEWED = "b2b_stock_viewed", "B2B stock viewed"
    REORDER_CLICKED = "reorder_clicked", "Reorder clicked"
    CUSTOMIZATION_STARTED = "customization_started", "Customization started"
    QUOTE_SIMULATED = "quote_simulated", "Quote simulated"
    QUOTE_REQUESTED = "quote_requested", "Quote requested"
    B2B_REQUEST_SUBMITTED = "b2b_request_submitted", "B2B request submitted"


class Event(models.Model):
    """A single tracked event with promoted KPI dimensions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=40, choices=EventTypeChoices.choices)

    # Optional link to a customer (anonymous events allowed).
    customer = models.ForeignKey(
        "accounts.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    # Promoted KPI dimensions (nullable so any event type can be stored).
    channel = models.CharField(
        max_length=3,
        choices=ChannelChoices.choices,
        blank=True,
        default="",
    )
    canton = models.CharField(max_length=2, blank=True, default="")
    campaign_period = models.CharField(max_length=50, blank=True, default="")
    value_chf = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # Flexible payload (sku list, qty, etc.).
    properties = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["channel", "created_at"]),
            models.Index(fields=["canton"]),
        ]

    def __str__(self):
        return f"{self.event_type} @{self.created_at:%Y-%m-%d %H:%M}"
