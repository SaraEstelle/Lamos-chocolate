"""
apps/backoffice/views.py
========================
Staff-only backoffice views: dashboard, orders, stock, B2B requests.

All views require an authenticated staff user (is_staff=True). We use
staff_member_required which redirects non-staff to the admin login.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.b2b.models import B2BRequest
from apps.backoffice.dashboards import (
    get_kpis,
    get_low_stock_items,
    get_revenue_last_30_days,
    get_top_products,
)
from apps.checkout.models import Order


@staff_member_required
@require_http_methods(["GET"])
def dashboard_view(request):
    """Backoffice home: KPIs + analytics."""
    context = {
        "kpis": get_kpis(),
        "revenue_30d": get_revenue_last_30_days(),
        "top_products": get_top_products(),
        "low_stock": get_low_stock_items(),
    }
    return render(request, "backoffice/dashboard.html", context)


@staff_member_required
@require_http_methods(["GET"])
def orders_list_view(request):
    """List all orders with optional status filter."""
    status = request.GET.get("status") or None
    orders = Order.objects.select_related("customer").order_by("-created_at")
    if status:
        orders = orders.filter(status=status)
    return render(request, "backoffice/orders.html", {
        "orders": orders,
        "current_status": status,
    })


@staff_member_required
@require_http_methods(["POST"])
def order_update_status_view(request, order_id):
    """Update an order's status from the backoffice."""
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get("status")
    valid = {"pending", "paid", "processing", "shipped", "delivered",
             "cancelled", "refunded"}
    if new_status in valid:
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
    return redirect("backoffice:orders")


@staff_member_required
@require_http_methods(["GET"])
def stock_view(request):
    """Show stock levels and low-stock alerts."""
    return render(request, "backoffice/stock.html", {
        "low_stock": get_low_stock_items(),
    })


@staff_member_required
@require_http_methods(["GET"])
def b2b_requests_view(request):
    """List B2B requests with optional status filter."""
    status = request.GET.get("status") or None
    requests_qs = B2BRequest.objects.order_by("-created_at")
    if status:
        requests_qs = requests_qs.filter(status=status)
    return render(request, "backoffice/b2b_requests.html", {
        "requests": requests_qs,
        "current_status": status,
    })


@staff_member_required
@require_http_methods(["POST"])
def b2b_update_status_view(request, request_id):
    """Update a B2B request status (new/in_progress/converted/refused)."""
    b2b = get_object_or_404(B2BRequest, id=request_id)
    new_status = request.POST.get("status")
    valid = {"new", "in_progress", "converted", "refused"}
    if new_status in valid:
        b2b.status = new_status
        b2b.processed_at = timezone.now()
        b2b.save(update_fields=["status", "processed_at"])
    return redirect("backoffice:b2b_requests")
