from django.db import models

# ============================================================
# 4.1 — Local choices + constants
# ============================================================


class CustomizationStatusChoices(models.TextChoices):
    """Lifecycle of a 4-axis customization request."""

    DRAFT = "draft", "Brouillon"
    QUOTE = "quote", "Devis demandé"
    ORDER = "order", "Commande"


class B2BAvailabilityChoices(models.TextChoices):
    """Pro-catalogue badge for a SKU."""

    ACTIVE = "active", "Actif"
    NEW = "new", "Nouveauté"
    COMING_SOON = "coming_soon", "Bientôt"


# Default minimum order quantity when a SKU has no explicit B2B MOQ.
DEFAULT_B2B_MOQ = 24


class B2BRequestStatusChoices(models.TextChoices):
    """Lifecycle of a B2B lead, managed from the backoffice."""

    NEW = "new", "Nouveau"
    IN_PROGRESS = "in_progress", "En cours"
    CONVERTED = "converted", "Converti"
    REFUSED = "refused", "Refusé"


# ============================================================
# Existing model — B2BRequest (completed with consent fields)
# ============================================================


class B2BRequest(models.Model):
    """
    Initial B2B contact request (a sales lead) sent from the public funnel.

    Contact/qualification fields are filled by B2BRequestForm.
    `ip_address`/`language` are set server-side (anti-abuse + i18n).
    `status`/`processed_at` are managed by the staff backoffice.
    """

    # --- Company & contact -------------------------------------------------
    company_name = models.CharField(max_length=120)
    contact_name = models.CharField(max_length=120, blank=True, default="")
    contact_email = models.EmailField()  # was: "email"
    contact_phone = models.CharField(max_length=40, blank=True, default="")

    # --- Qualification of the lead ----------------------------------------
    sector = models.CharField(max_length=120, blank=True, default="")
    estimated_qty = models.PositiveIntegerField(null=True, blank=True)
    occasion = models.CharField(max_length=120, blank=True, default="")
    message = models.TextField(blank=True, default="")

    # --- Set server-side (never trust the client) -------------------------
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    language = models.CharField(max_length=5, blank=True, default="fr")

    # --- Lead lifecycle (managed in the backoffice) -----------------------
    status = models.CharField(
        max_length=20,
        choices=B2BRequestStatusChoices.choices,
        default=B2BRequestStatusChoices.NEW,
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # --- Marketing consent (nLPD): optional opt-in, stored with a timestamp.
    wants_marketing = models.BooleanField(default=False)
    marketing_consent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "b2b_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"B2BRequest{self.contact_email} ({self.company_name})"


# ============================================================
# 4.1 — New models
# ============================================================


class B2BProductInfo(models.Model):
    """
    B2B-specific data for a catalog SKU (kept in the b2b app on purpose,
    so the B2C catalog stays untouched). Drives the pro catalogue, MOQ
    and pro pricing.
    """

    sku = models.OneToOneField(
        "shop.SKU",
        on_delete=models.CASCADE,
        related_name="b2b_info",
    )
    is_b2b_available = models.BooleanField(default=True)
    availability_status = models.CharField(
        max_length=20,
        choices=B2BAvailabilityChoices.choices,
        default=B2BAvailabilityChoices.ACTIVE,
    )
    moq = models.PositiveIntegerField(
        default=DEFAULT_B2B_MOQ,
        help_text="Minimum order quantity for B2B",
    )
    b2b_unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Pro unit price in CHF; falls back to the SKU price if empty",
    )

    class Meta:
        db_table = "b2b_product_info"

    def __str__(self):
        return f"B2B info —{self.sku.sku_code} (MOQ{self.moq})"

    @property
    def effective_price(self):
        """Pro price if set, otherwise the standard SKU price."""
        return (
            self.b2b_unit_price if self.b2b_unit_price is not None else self.sku.price
        )


class CustomizationRequest(models.Model):
    """A 4-axis personalisation request attached to a pro account."""

    account = models.ForeignKey(
        "accounts.B2BAccount",
        on_delete=models.CASCADE,
        related_name="customization_requests",
    )
    sku = models.ForeignKey(
        "shop.SKU",
        on_delete=models.PROTECT,
        related_name="customization_requests",
    )

    # The 4 traceable axes (each is a real column for KPI aggregation).
    logo_engraved = models.BooleanField(default=False)
    inner_packaging = models.CharField(max_length=120, blank=True, default="")
    outer_packaging = models.CharField(max_length=120, blank=True, default="")
    grammage = models.PositiveIntegerField(null=True, blank=True)

    quantity = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=CustomizationStatusChoices.choices,
        default=CustomizationStatusChoices.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "b2b_customization_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Customization{self.sku.sku_code} x{self.quantity} ({self.status})"


class QuoteSimulation(models.Model):
    """A MOQ-aware quote simulation (feeds the B2B pipeline KPIs)."""

    account = models.ForeignKey(
        "accounts.B2BAccount",
        on_delete=models.CASCADE,
        related_name="quote_simulations",
    )
    # Snapshot of the simulated cart: list of {"sku": code, "qty": n, "price": p}.
    cart_json = models.JSONField(default=list, blank=True)
    moq_reached = models.BooleanField(default=False)
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    converted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "b2b_quote_simulations"
        ordering = ["-created_at"]

    def __str__(self):
        flag = "≥MOQ" if self.moq_reached else "<MOQ"
        return f"Quote{self.estimated_value} CHF ({flag})"
