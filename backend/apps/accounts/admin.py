from django.contrib import admin

from .models import Customer, PasswordResetToken


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "is_active", "created_at")
    list_filter = ("is_active", "language_pref")
    search_fields = ("email", "first_name", "last_name")
    exclude = ("password_hash",)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("customer", "expires_at", "used", "created_at")
    list_filter = ("used",)
    search_fields = ("customer__email",)
