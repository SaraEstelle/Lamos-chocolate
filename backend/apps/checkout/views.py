"""
apps/checkout/views.py
======================
HTTP layer for the checkout flow: the checkout page, Stripe session creation,
and the success/cancel return pages. The webhook handler lives in webhooks.py.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST

from apps.cart.cart import Cart
from apps.cart.services import calculate_total
from apps.common.constants import ChannelChoices

from .forms import ShippingForm
from .stripe import create_checkout_session


@login_required(login_url="accounts:login")
@require_GET
def checkout_view(request):
    """Render the checkout page: order summary plus the shipping form."""
    cart = Cart(request)
    if cart.is_empty:
        messages.info(request, _("Your cart is empty."))
        return redirect("cart:view")

    form = ShippingForm(
        initial={
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
        }
    )
    return render(request, "checkout/checkout.html", _checkout_context(cart, form))


@login_required(login_url="accounts:login")
@require_POST
def create_checkout_session_view(request):
    """Validate the shipping form and hand off to Stripe Checkout."""
    cart = Cart(request)
    if cart.is_empty:
        messages.info(request, _("Your cart is empty."))
        return redirect("cart:view")

    form = ShippingForm(request.POST)
    if not form.is_valid():
        return render(request, "checkout/checkout.html", _checkout_context(cart, form))

    cart_items = list(cart)
    session = create_checkout_session(
        customer=request.user,
        cart_items=cart_items,
        shipping=form.as_shipping_dict(),
        currency=cart_items[0].sku.currency,
        language=get_language() or "fr",
        channel=ChannelChoices.B2C,
        success_url=(
            request.build_absolute_uri(reverse("checkout:success"))
            + "?session_id={CHECKOUT_SESSION_ID}"
        ),
        cancel_url=request.build_absolute_uri(reverse("checkout:cancel")),
    )
    return redirect(session.url)


@require_GET
def success_view(request):
    """Thank-you page shown after Stripe redirects back on payment success.

    The order itself is created asynchronously by the webhook, so we only clear
    the visitor's session cart here and confirm the payment is being processed.
    """
    Cart(request).clear()
    return render(request, "checkout/success.html")


@require_GET
def cancel_view(request):
    """Shown when the customer cancels at Stripe; the cart is left untouched."""
    return render(request, "checkout/cancel.html")


def _checkout_context(cart, form):
    return {
        "cart_items": list(cart),
        "cart_total": calculate_total(cart),
        "cart_count": len(cart),
        "form": form,
    }
