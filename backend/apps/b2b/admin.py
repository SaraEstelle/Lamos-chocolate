from django.contrib import admin
from .models import B2BRequest


@admin.register(B2BRequest)
class B2BRequestAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "email",
        "created_at",
        "wants_marketing",
    )
    list_filter = ("wants_marketing",)
    search_fields = ("company_name", "email")
    readonly_fields = ("created_at", "marketing_consent_at")
