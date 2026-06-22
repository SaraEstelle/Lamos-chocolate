"""Cart HTTP layer.

``cart_view`` renders the full cart page. ``add_item_view``,
``update_item_view`` and ``remove_item_view`` are POST endpoints that work in
two modes:

* a regular HTML form POST (e.g. the shop product page) → mutate the cart then
  Post/Redirect/Get back to the cart page, surfacing feedback via Django
  messages;
* an AJAX/JSON request (``X-Requested-With: XMLHttpRequest`` or
  ``Accept: application/json``) → return the serialized cart as JSON.
"""

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST

from .cart import Cart
from .serializers import serialize_cart
from .services import add_to_cart, calculate_total, remove_from_cart, update_quantity


def _wants_json(request) -> bool:
    return (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or request.headers.get("accept", "").startswith("application/json")
    )


def _respond(request, cart, *, message=None, error=None):
    if _wants_json(request):
        payload = serialize_cart(cart, request.LANGUAGE_CODE)
        if error:
            payload["error"] = error
            return JsonResponse(payload, status=400)
        return JsonResponse(payload)

    if error:
        messages.error(request, error)
    elif message:
        messages.success(request, message)
    return redirect("cart:view")


@require_GET
def cart_view(request):
    cart = Cart(request)
    context = {
        "cart_items": list(cart),
        "cart_total": calculate_total(cart),
        "cart_count": len(cart),
    }
    return render(request, "cart/cart.html", context)


@require_POST
def add_item_view(request):
    cart = Cart(request)
    try:
        add_to_cart(cart, request.POST.get("sku_id"), request.POST.get("quantity", 1))
    except ValueError as exc:
        return _respond(request, cart, error=str(exc))
    return _respond(request, cart, message=_("Item added to your cart."))


@require_POST
def update_item_view(request):
    cart = Cart(request)
    try:
        update_quantity(cart, request.POST.get("sku_id"), request.POST.get("quantity"))
    except ValueError as exc:
        return _respond(request, cart, error=str(exc))
    return _respond(request, cart, message=_("Cart updated."))


@require_POST
def remove_item_view(request):
    cart = Cart(request)
    remove_from_cart(cart, request.POST.get("sku_id"))
    return _respond(request, cart, message=_("Item removed from your cart."))
