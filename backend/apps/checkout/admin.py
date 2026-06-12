from django.contrib import admin

from .models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("subtotal",)


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer",
        "status",
        "total_amount",
        "currency",
        "created_at",
    )
    list_filter = ("status", "currency")
    search_fields = ("order_number", "customer__email")
    inlines = [OrderItemInline, PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "stripe_payment_intent", "amount", "currency", "status")
    list_filter = ("status", "currency")
    search_fields = ("order__order_number", "stripe_payment_intent")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "sku", "quantity", "unit_price", "subtotal")
    search_fields = ("order__order_number", "sku__sku_code")
