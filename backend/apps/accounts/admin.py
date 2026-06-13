"""
apps/accounts/admin.py
======================
Django admin interface for Customer and PasswordResetToken.

Allows staff/superusers to:
- See all customers
- Search by email
- Filter by is_active, is_staff
- Edit information
- View created_at, updated_at dates
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Customer, PasswordResetToken


@admin.register(Customer)
class CustomerAdmin(BaseUserAdmin):
    """
    Admin interface for Customer.

    Display:
    - List: email, first_name, is_active, created_at
    - Search: email, first_name, last_name
    - Filters: is_active, is_staff, preferred_language
    """

    # TEMPORARY FIX:
    # Disable filter_horizontal because Customer does NOT inherit PermissionsMixin yet.
    # This will be restored in Phase 3 when groups/user_permissions exist.
    filter_horizontal = ()

    # Fields displayed in list
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'created_at')

    # Fields where you can click to edit
    list_display_links = ('email', 'first_name')

    # Filters on the left
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'preferred_language', 'created_at')

    # Search fields
    search_fields = ('email', 'first_name', 'last_name', 'phone')

    # Read-only fields
    readonly_fields = ('created_at', 'updated_at', 'id')

    # Organization of fields
    fieldsets = (
        ('Authentication', {
            'fields': ('id', 'email', 'password')
        }),
        ('Personal information', {
            'fields': ('first_name', 'last_name', 'phone', 'company_name')
        }),
        ('Preferences', {
            'fields': ('preferred_language', 'is_b2b')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Field order when creating
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name')
        }),
    )

    # Default sort (most recent first)
    ordering = ('-created_at',)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """
    Admin interface for PasswordResetToken.

    Display reset tokens created for password resets.
    """

    list_display = ('customer', 'is_used', 'expires_at', 'created_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('customer__email', 'token')
    readonly_fields = ('token', 'created_at', 'customer')

    # Tokens cannot be added
    def has_add_permission(self, request):
        return False

    # Only superuser can delete
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser