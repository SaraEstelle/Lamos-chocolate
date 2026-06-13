from django.db import models

from apps.common.constants import B2BStatusChoices, LanguageChoices


class B2BRequest(models.Model):
    company_name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=200)
    contact_email = models.EmailField(max_length=255)
    contact_phone = models.CharField(max_length=30, blank=True, default="")
    sector = models.CharField(max_length=100, blank=True, default="")
    estimated_qty = models.PositiveIntegerField(null=True, blank=True)
    occasion = models.CharField(max_length=200, blank=True, default="")
    message = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=B2BStatusChoices.choices,
        default=B2BStatusChoices.NEW,
    )
    language = models.CharField(
        max_length=2,
        choices=LanguageChoices.choices,
        default=LanguageChoices.FR,
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        "backoffice.AdminUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "b2b_requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"B2B — {self.company_name} ({self.status})"
