"""
apps/b2b/views.py
=================
B2B views: L0 public funnel + L1 pro space + L2 configurator.
"""

from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from apps.analytics.services import track_event
from apps.b2b.decorators import b2b_account_required
from apps.b2b.forms import B2BRequestForm
from apps.b2b.selectors import has_recent_duplicate
from apps.b2b.services import create_b2b_request, get_client_ip, is_rate_limited

from apps.b2b.models import QuoteSimulation
from apps.b2b.selectors import get_b2b_orders, get_pro_catalogue
from apps.b2b.services import notify_quote_request, simulate_quote
from apps.checkout.models import Order

from apps.b2b.forms import ConfiguratorForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from apps.b2b.forms import B2BRegisterForm
from apps.b2b.services import notify_b2b_account_pending  # email hook (Guide 3 wires SMTP)

@require_http_methods(["GET", "POST"])
def register_view(request):
    """Method 1: a professional creates their own (pending) account."""
    if request.method == "POST":
        form = B2BRegisterForm(request.POST)
        if form.is_valid():
            customer, account = form.save()
            notify_b2b_account_pending(account)      # email staff + applicant
            login(request, customer,
                  backend="django.contrib.auth.backends.ModelBackend")
            return redirect("b2b:pending")
    else:
        form = B2BRegisterForm()
    return render(request, "b2b/register.html", {"form": form})


@login_required(login_url="accounts:login")
@require_http_methods(["GET"])
def pending_view(request):
    """Shown while a pro account awaits validation."""
    account = getattr(request.user, "b2b_account", None)
    if account and account.status == "active":
        return redirect("b2b:portal")          # already validated
    return render(request, "b2b/pending.html", {"account": account})
# ----------------------------------------------------------------------------
# L0 — Public funnel (no login)
# ----------------------------------------------------------------------------
@require_http_methods(["GET"])
def presentation_view(request):
    """Public B2B landing page (corporate gifting + 4-axis teaser)."""
    return render(request, "b2b/presentation.html")


@require_http_methods(["GET", "POST"])
def request_form_view(request):
    """Display and handle the professional request form."""
    if request.method == "POST":
        form = B2BRequestForm(data=request.POST)
        if form.is_valid():
            if form.is_bot():                       # honeypot → fake success
                return redirect("b2b:success")
            ip = get_client_ip(request)
            if is_rate_limited(ip):                 # flood protection
                messages.error(request, _("Too many requests. Please try again later."))
                return render(request, "b2b/request_form.html", {"form": form})
            if has_recent_duplicate(                # double-submit guard
                contact_email=form.cleaned_data["contact_email"],
                company_name=form.cleaned_data["company_name"],
            ):
                messages.info(request, _("We already received your request."))
                return redirect("b2b:success")
            create_b2b_request(form, request=request)
            messages.success(request, _("Your request has been sent. Thank you!"))
            return redirect("b2b:success")
    else:
        form = B2BRequestForm()
    return render(request, "b2b/request_form.html", {"form": form})


@require_http_methods(["GET"])
def success_view(request):
    """Confirmation page after submission."""
    return render(request, "b2b/success.html")


# ----------------------------------------------------------------------------
# L1 — Pro space (login + B2BAccount required)
# ----------------------------------------------------------------------------
@b2b_account_required
@require_http_methods(["GET"])
def portal_home_view(request):
    """Pro portal home: greeting + a few recent orders + catalogue preview."""
    account = request.b2b_account
    return render(request, "b2b/portal/home.html", {
        "account": account,
        "catalogue": get_pro_catalogue()[:6],
        "orders": get_b2b_orders(account, limit=5),
    })


@b2b_account_required
@require_http_methods(["GET"])
def portal_catalogue_view(request):
    """Pro catalogue with real-time stock per SKU."""
    account = request.b2b_account
    # The pro consulted live stock → track it (feeds B2B engagement KPIs).
    track_event("b2b_stock_viewed", customer=request.user, channel="b2b",
                account=str(account.id))
    return render(request, "b2b/portal/catalogue.html", {
        "account": account, "catalogue": get_pro_catalogue(),
    })


@b2b_account_required
@require_http_methods(["GET"])
def portal_history_view(request):
    """Pro order history (scoped to the account owner)."""
    account = request.b2b_account
    return render(request, "b2b/portal/history.html", {
        "account": account, "orders": get_b2b_orders(account),
    })


@b2b_account_required
@require_http_methods(["POST"])
def reorder_view(request, order_id):
    """
    1-click reorder: build a draft quote from a past B2B order.

    Decoupled from the cart (still in progress): a prior order is, by definition,
    above MOQ, so we create a ready-to-confirm QuoteSimulation and let sales
    validate pricing (matches the PRD's human-validated B2B flow).
    """
    account = request.b2b_account
    # Order.id is a BigAutoField (int). Scope to the owner to prevent IDOR.
    order = get_object_or_404(
        Order, id=order_id, customer=account.customer, channel="b2b",
    )
    lines = [
        {"sku": it.sku.sku_code, "qty": it.quantity, "price": str(it.unit_price)}
        for it in order.items.all()
    ]
    estimated = sum(Decimal(line["price"]) * line["qty"] for line in lines)
    QuoteSimulation.objects.create(
        account=account, cart_json=lines, estimated_value=estimated, moq_reached=True,
    )
    track_event("reorder_clicked", customer=request.user, channel="b2b",
                order_id=order.order_number, value_chf=estimated)
    messages.success(request, _("Reorder prepared. Our team will confirm pricing."))
    return redirect("b2b:history")


# ----------------------------------------------------------------------------
# L2 — Configurator (4 axes) + MOQ simulator + quote request
# ----------------------------------------------------------------------------
@b2b_account_required
@require_http_methods(["GET", "POST"])
def configurator_view(request):
    """
    4-axis configurator with a MOQ-aware quote simulator.

    Two POST actions (via the submit button's name="action"):
    - "simulate"      → compute value + MOQ status, persist a QuoteSimulation
    - "request_quote" → also create the CustomizationRequest and email sales
    """
    account = request.b2b_account
    simulation = None

    if request.method == "POST":
        form = ConfiguratorForm(data=request.POST)
        if form.is_valid():
            sku = form.cleaned_data["sku"]
            qty = form.cleaned_data["quantity"]
            simulation = simulate_quote(account, sku=sku, quantity=qty)
            track_event(
                "quote_simulated", customer=request.user, channel="b2b",
                value_chf=simulation["estimated"],
                moq_reached=simulation["moq_reached"], sku=sku.sku_code,
            )

            if request.POST.get("action") == "request_quote":
                customization = form.save(commit=False)
                customization.account = account
                customization.status = "quote"
                customization.save()
                simulation["sim"].converted = True
                simulation["sim"].save(update_fields=["converted"])
                notify_quote_request(account, customization, simulation["estimated"])
                track_event(
                    "quote_requested", customer=request.user, channel="b2b",
                    value_chf=simulation["estimated"], sku=sku.sku_code,
                )
                messages.success(request, _("Quote requested. Our team will contact you."))
                return redirect("b2b:configurator")
    else:
        form = ConfiguratorForm()
        # Opening the configurator is the start of a customization journey.
        track_event("customization_started", customer=request.user, channel="b2b")

    return render(request, "b2b/configurator.html", {
        "account": account, "form": form, "simulation": simulation,
    })

@b2b_account_required
@require_http_methods(["GET"])
def documents_view(request):
    """Pro documents (invoices/quotes). Reuses orders + quote simulations."""
    account = request.b2b_account
    return render(request, "b2b/portal/documents.html", {
        "account": account,
        "orders": get_b2b_orders(account),
        "quotes": account.quote_simulations.all()[:20],
    })

@b2b_account_required
@require_http_methods(["GET"])
def notifications_view(request):
    """Account-level notifications (validation, quote status…)."""
    return render(request, "b2b/portal/notifications.html", {"account": request.b2b_account})

@b2b_account_required
@require_http_methods(["GET", "POST"])
def company_profile_view(request):
    """Edit company info (name, payment terms read-only for the pro)."""
    account = request.b2b_account
    if request.method == "POST":
        account.company_name = request.POST.get("company_name", account.company_name).strip()
        account.save(update_fields=["company_name"])
        messages.success(request, _("Company profile updated."))
        return redirect("b2b:profile")
    return render(request, "b2b/portal/profile.html", {"account": account})