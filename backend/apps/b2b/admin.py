from django.contrib import admin

from .models import B2BRequest


@admin.register(B2BRequest)
class B2BRequestAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "contact_email",
        "status",
        "created_at",
        "processed_by",
    )
    list_filter = ("status",)
    search_fields = ("company_name", "contact_email", "contact_name")
    readonly_fields = ("ip_address", "created_at")
