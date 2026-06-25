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
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator

from apps.accounts.forms import ProfileForm
from apps.customer_area.selectors import (
    get_customer_dashboard_stats,
    get_customer_order_or_none,
    get_customer_orders,
)

from apps.customer_area.forms import AddressForm
from apps.customer_area.models import CustomerAddress
from apps.customer_area.selectors import (
    get_customer_addresses,
    get_filtered_customer_orders,
)
from django.contrib.auth import update_session_auth_hash
from apps.accounts.forms import PasswordChangeForm
from apps.checkout.models import Order


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


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def orders_view(request):
    """List the customer's orders with optional status filter + pagination."""
    status = request.GET.get("status") or None
    orders_qs = get_filtered_customer_orders(request.user, status=status)

    paginator = Paginator(orders_qs, 10)  # 10 orders per page
    page = paginator.get_page(request.GET.get("page"))

    context = {
        "orders": page,
        "current_status": status,
    }
    return render(request, "customer_area/orders.html", context)


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def addresses_view(request):
    """List the customer's saved addresses."""
    addresses = get_customer_addresses(request.user)
    return render(request, "customer_area/addresses.html", {"addresses": addresses})


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def address_create_view(request):
    """Create a new saved address."""
    if request.method == "POST":
        form = AddressForm(data=request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.customer = request.user
            address.save()
            messages.success(request, _("Address saved."))
            return redirect("customer_area:addresses")
    else:
        form = AddressForm()
    return render(request, "customer_area/address_form.html", {"form": form})


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def address_edit_view(request, address_id):
    """Edit an existing address (scoped to the customer)."""
    address = get_object_or_404(
        CustomerAddress, id=address_id, customer=request.user
    )
    if request.method == "POST":
        form = AddressForm(data=request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, _("Address updated."))
            return redirect("customer_area:addresses")
    else:
        form = AddressForm(instance=address)
    return render(request, "customer_area/address_form.html", {"form": form})


@login_required(login_url="accounts:login")
@require_http_methods(["POST"])
def address_delete_view(request, address_id):
    """Delete an address (scoped to the customer)."""
    address = get_object_or_404(
        CustomerAddress, id=address_id, customer=request.user
    )
    address.delete()
    messages.success(request, _("Address deleted."))
    return redirect("customer_area:addresses")

@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def password_change_view(request):
    """Let a logged-in customer change their password (keeps them logged in)."""
    if request.method == "POST":
        form = PasswordChangeForm(request.POST, user=request.user)
        if form.is_valid():
            request.user.set_password(form.cleaned_data["new_password"])
            request.user.save(update_fields=["password"])
            update_session_auth_hash(request, request.user)  # avoid logout
            messages.success(request, _("Your password has been updated."))
            return redirect("customer_area:password_change")
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, "customer_area/password_change.html", {"form": form})

@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def invoices_view(request):
    """List the customer's billable orders (paid)."""
    orders = (Order.objects
              .filter(customer=request.user, status__in=["paid", "shipped", "delivered"])
              .order_by("-created_at"))
    return render(request, "customer_area/invoices.html", {"orders": orders})

@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def invoice_detail_view(request, order_id):
    """Printable invoice, scoped to the owner (prevents IDOR)."""
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, "customer_area/invoice_detail.html", {"order": order})