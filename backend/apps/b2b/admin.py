from django.contrib import admin
from .models import (
    B2BRequest,
    B2BProductInfo,
    CustomizationRequest,
    QuoteSimulation,
)


@admin.register(B2BRequest)
class B2BRequestAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "contact_name",     # now available
        "contact_email",    # was "email"
        "status",
        "created_at",
        "wants_marketing",
    )
    list_filter = ("status", "wants_marketing",)
    search_fields = ("company_name", "contact_email")   # was "email"
    readonly_fields = ("ip_address", "created_at", "processed_at", "marketing_consent_at")

@admin.register(B2BProductInfo)
class B2BProductInfoAdmin(admin.ModelAdmin):
    list_display = ("sku", "moq", "b2b_unit_price", "availability_status", "is_b2b_available")
    list_filter = ("availability_status", "is_b2b_available")
    search_fields = ("sku__sku_code",)


@admin.register(CustomizationRequest)
class CustomizationRequestAdmin(admin.ModelAdmin):
    list_display = ("account", "sku", "quantity", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("account__company_name", "sku__sku_code")


@admin.register(QuoteSimulation)
class QuoteSimulationAdmin(admin.ModelAdmin):
    list_display = ("account", "estimated_value", "moq_reached", "converted", "created_at")
    list_filter = ("moq_reached", "converted")