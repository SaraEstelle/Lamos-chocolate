"""
apps/accounts/admin.py
======================
Django admin interface for Customer and PasswordResetToken.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Customer, PasswordResetToken


@admin.register(Customer)
class CustomerAdmin(BaseUserAdmin):
    """Admin for Customer (full Django auth support via PermissionsMixin)."""

    # List view
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_b2b",
        "is_active",
        "is_staff",
        "created_at",
    )
    list_display_links = ("email", "first_name")
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "is_b2b",
        "preferred_language",
        "created_at",
    )
    search_fields = ("email", "first_name", "last_name", "phone", "company_name")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at", "last_login")

    # Detail view (override BaseUserAdmin defaults to match our fields)
    fieldsets = (
        (_("Identity"), {
            "fields": ("id", "email", "password"),
        }),
        (_("Personal"), {
            "fields": ("first_name", "last_name", "phone"),
        }),
        (_("Business"), {
            "fields": ("is_b2b", "company_name"),
        }),
        (_("Preferences"), {
            "fields": ("preferred_language",),
        }),
        (_("Permissions"), {
            "fields": (
                "is_active", "is_staff", "is_superuser",
                "groups", "user_permissions",
            ),
        }),
        (_("Dates"), {
            "fields": ("created_at", "updated_at", "last_login"),
            "classes": ("collapse",),
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "password1", "password2",
                "first_name", "last_name",
            ),
        }),
    )

    filter_horizontal = ("groups", "user_permissions")


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("customer", "is_used", "expires_at", "created_at")
    list_filter = ("is_used", "created_at")
    search_fields = ("customer__email", "token")
    readonly_fields = ("id", "token", "created_at", "customer")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser