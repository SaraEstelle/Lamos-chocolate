"""
apps/main/views.py
==================
Public marketing and static pages (no authentication required).

Views:
- home_view    : landing page (hero + featured products)
- about_view   : about the brand
- privacy_view : privacy policy (GDPR / Swiss nLPD)
- terms_view   : terms of service
- contact_view : contact form
"""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from apps.main.forms import ContactForm
from apps.shop.selectors import get_active_products, get_all_categories


@require_http_methods(["GET"])
def home_view(request):
    """Landing page: hero + a few featured products."""
    featured = get_active_products()[:3]      # selector already eager-loads images
    categories = get_all_categories()
    context = {
        "featured": featured,
        "categories": categories,
    }
    return render(request, "main/home.html", context)


@require_http_methods(["GET"])
def about_view(request):
    """Brand story / about page."""
    return render(request, "main/about.html")


@require_http_methods(["GET"])
def privacy_view(request):
    """Privacy policy (GDPR / Swiss nLPD)."""
    return render(request, "main/privacy.html")


@require_http_methods(["GET"])
def terms_view(request):
    """Terms of service."""
    return render(request, "main/terms.html")


@require_http_methods(["GET", "POST"])
def contact_view(request):
    """Contact form: display and handle submission."""
    if request.method == "POST":
        form = ContactForm(data=request.POST)
        if form.is_valid():
            # For now we only acknowledge; real email wiring comes later.
            messages.success(request, _("Your message has been sent. Thank you!"))
            return redirect("main:contact")
    else:
        form = ContactForm()
    return render(request, "main/contact.html", {"form": form})
