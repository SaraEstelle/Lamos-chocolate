from django.contrib import admin

from .models import SKU, Category, Product, ShippingZone, Stock


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name_fr", "name_en", "slug")
    prepopulated_fields = {"slug": ("name_en",)}
    search_fields = ("name_fr", "name_en")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name_fr", "category", "is_active", "created_at")
    list_filter = ("is_active", "category")
    search_fields = ("name_fr", "name_en", "slug")
    prepopulated_fields = {"slug": ("name_en",)}


@admin.register(SKU)
class SKUAdmin(admin.ModelAdmin):
    list_display = ("sku_code", "product", "format", "price", "currency", "is_active")
    list_filter = ("currency", "is_active")
    search_fields = ("sku_code", "product__name_fr")


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("sku", "quantity", "threshold_alert", "is_low", "updated_at")
    search_fields = ("sku__sku_code",)


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ("zone_name", "delay_days", "cost")
