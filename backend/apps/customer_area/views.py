"""
apps/customer_area/views.py
===========================
Views for the authenticated customer area.

All views require login. Each view scopes data to request.user so a
customer can only ever see their own information.

Views:
- dashboard_view       : account home (greeting + quick stats)
- orders_view          : list of the customer's orders
- order_detail_view    : details of a single order (scoped to the customer)
- profile_view         : view / edit personal information
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from apps.accounts.forms import ProfileForm
from apps.customer_area.selectors import (
    get_customer_dashboard_stats,
    get_customer_order_or_none,
    get_customer_orders,
)


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def dashboard_view(request):
    """Account home: greeting + quick stats."""
    stats = get_customer_dashboard_stats(request.user)
    context = {
        "customer": request.user,
        "stats": stats,
    }
    return render(request, "customer_area/dashboard.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def orders_view(request):
    """List all orders belonging to the logged-in customer."""
    orders = get_customer_orders(request.user)
    return render(request, "customer_area/orders.html", {"orders": orders})


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def order_detail_view(request, order_id):
    """
    Show one order. Redirect if the order does not belong to the customer
    (prevents accessing other customers' orders by guessing the id).
    """
    order = get_customer_order_or_none(request.user, order_id)
    if order is None:
        # Do not reveal whether the id exists for another customer
        messages.error(request, _("Order not found."))
        return redirect("customer_area:orders")
    return render(request, "customer_area/order_detail.html", {"order": order})


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def profile_view(request):
    """View and edit the customer's personal information."""
    if request.method == "POST":
        form = ProfileForm(data=request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Your profile has been updated."))
            return redirect("customer_area:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "customer_area/profile.html", {"form": form})