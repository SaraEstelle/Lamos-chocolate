"""
apps/accounts/admin.py
======================
Django admin interface for Customer and PasswordResetToken.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import B2BAccount  # add near the other imports
from apps.b2b.services import notify_b2b_account_validated  # email hook (Guide 3)
from apps.common.constants import B2BAccountStatusChoices

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
        (
            _("Identity"),
            {
                "fields": ("id", "email", "password"),
            },
        ),
        (
            _("Personal"),
            {
                "fields": ("first_name", "last_name", "phone"),
            },
        ),
        (
            _("Business"),
            {
                "fields": ("is_b2b", "company_name"),
            },
        ),
        (
            _("Preferences"),
            {
                "fields": ("preferred_language",),
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            _("Dates"),
            {
                "fields": ("created_at", "updated_at", "last_login"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Segmentation & KPI"),
            {
                "fields": ("customer_type", "npa", "canton", "source_acquisition"),
            },
        ),
        (
            _("Consent (nLPD)"),
            {
                "fields": ("consent_nlpd", "consent_nlpd_at"),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                ),
            },
        ),
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


@admin.register(B2BAccount)
class B2BAccountAdmin(admin.ModelAdmin):
    list_display = ("company_name", "segment", "status", "client_number")
    list_filter = ("segment", "status")
    search_fields = ("company_name", "client_number")
    actions = ["approve_accounts"]

    @admin.action(description="Approve selected B2B accounts (activate + notify)")
    def approve_accounts(self, request, queryset):
        for account in queryset.exclude(status=B2BAccountStatusChoices.ACTIVE):
            account.status = B2BAccountStatusChoices.ACTIVE
            account.onboarded_at = timezone.now()
            account.save(update_fields=["status", "onboarded_at"])
            notify_b2b_account_validated(account)
        self.message_user(request, "Selected accounts approved and notified.")
