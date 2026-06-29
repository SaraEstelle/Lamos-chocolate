from django.conf import settings


def feature_flags(request):
    fb = settings.SOCIALACCOUNT_PROVIDERS.get("facebook", {}).get("APP", {})
    return {"FACEBOOK_ENABLED": bool(fb.get("client_id"))}


def cart_summary(request):
    """Expose the session cart count and total on every page (navbar badge)."""
    from apps.cart.cart import Cart
    from apps.cart.services import calculate_total

    cart = Cart(request)
    return {"cart_count": len(cart), "cart_total": calculate_total(cart)}
