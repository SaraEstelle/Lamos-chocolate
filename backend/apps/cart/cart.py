"""Session-based shopping cart.

The cart lives entirely in ``request.session`` so anonymous visitors can shop
without an account. Prices are read live from the related SKU on each request;
the immutable price snapshot only happens later at checkout (``OrderItem``).

Session layout::

    request.session["cart"] = {
        "<sku_id>": {"quantity": <int>},
        ...
    }
"""

from dataclasses import dataclass
from decimal import Decimal

from django.utils.translation import get_language

from apps.shop.models import SKU

CART_SESSION_KEY = "cart"


@dataclass
class CartItem:
    """A single cart line, resolved against the live SKU."""

    sku: SKU
    quantity: int

    @property
    def display_name(self) -> str:
        """Product name in the request's active language (falls back to French)."""
        return self.sku.product.get_name(get_language() or "fr")

    @property
    def unit_price(self) -> Decimal:
        return self.sku.price

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


class Cart:
    """Thin wrapper around the session dict holding cart lines.

    Only raw storage and iteration live here. Business rules (stock checks,
    SKU validation) are handled in ``services.py``.
    """

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = self.session[CART_SESSION_KEY] = {}
        self._cart = cart

    def save(self):
        """Persist changes by flagging the session as modified."""
        self.session.modified = True

    def set_quantity(self, sku_id, quantity):
        """Store an absolute quantity for ``sku_id`` (low-level, no validation)."""
        self._cart[str(sku_id)] = {"quantity": quantity}
        self.save()

    def get_quantity(self, sku_id) -> int:
        line = self._cart.get(str(sku_id))
        return line["quantity"] if line else 0

    def remove(self, sku_id):
        """Drop a line from the cart if present."""
        key = str(sku_id)
        if key in self._cart:
            del self._cart[key]
            self.save()

    def clear(self):
        self.session[CART_SESSION_KEY] = self._cart = {}
        self.save()

    def __contains__(self, sku_id):
        return str(sku_id) in self._cart

    def __iter__(self):
        """Yield ``CartItem`` objects, loading SKUs in a single query.

        Lines whose SKU no longer exists or is inactive are skipped silently.
        """
        sku_ids = [int(sku_id) for sku_id in self._cart]
        skus = SKU.objects.filter(id__in=sku_ids, is_active=True).select_related(
            "product"
        )
        skus_by_id = {sku.id: sku for sku in skus}

        for sku_id, line in self._cart.items():
            sku = skus_by_id.get(int(sku_id))
            if sku is not None:
                yield CartItem(sku=sku, quantity=line["quantity"])

    def __len__(self) -> int:
        """Total number of units across all lines."""
        return sum(line["quantity"] for line in self._cart.values())

    @property
    def is_empty(self) -> bool:
        return not self._cart
