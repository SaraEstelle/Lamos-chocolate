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