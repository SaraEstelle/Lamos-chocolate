"""Plain-Python serialization of the cart for JSON (AJAX) responses.

No DRF in this project, so we hand-build JSON-safe dicts (Decimals -> str to
preserve exact monetary values).
"""

from .cart import Cart, CartItem
from .services import calculate_total


def serialize_item(item: CartItem, lang: str = "fr") -> dict:
    sku = item.sku
    return {
        "sku_id": sku.id,
        "sku_code": sku.sku_code,
        "product_name": sku.product.get_name(lang),
        "format": sku.format,
        "unit_price": str(item.unit_price),
        "currency": sku.currency,
        "quantity": item.quantity,
        "subtotal": str(item.subtotal),
    }


def serialize_cart(cart: Cart, lang: str = "fr") -> dict:
    items = [serialize_item(item, lang) for item in cart]
    return {
        "items": items,
        "total_items": len(cart),
        "total_price": str(calculate_total(cart)),
        "is_empty": cart.is_empty,
    }
