"""Cart business operations.

These functions own the validation rules (SKU exists/active, positive
quantity, stock availability) and delegate raw storage to :class:`Cart`.
They raise ``ValueError`` on invalid input, mirroring the convention used by
``shop.models.Stock`` so views can translate failures into HTTP responses.
"""

from decimal import Decimal

from apps.shop.models import SKU

from .cart import Cart


def _get_active_sku(sku_id) -> SKU:
    try:
        return SKU.objects.select_related("stock").get(id=sku_id, is_active=True)
    except (SKU.DoesNotExist, ValueError, TypeError):
        raise ValueError(f"SKU {sku_id} not found or inactive.")


def _available_stock(sku: SKU) -> int:
    stock = getattr(sku, "stock", None)
    return stock.quantity if stock is not None else 0


def add_to_cart(cart: Cart, sku_id, quantity: int = 1) -> SKU:
    """Add ``quantity`` units of an SKU, summing with what is already there.

    Returns the resolved SKU. Raises ``ValueError`` if the SKU is invalid,
    the quantity is not a positive integer, or stock is insufficient.
    """
    quantity = _validate_quantity(quantity)
    sku = _get_active_sku(sku_id)

    new_quantity = cart.get_quantity(sku.id) + quantity
    if new_quantity > _available_stock(sku):
        raise ValueError(
            f"Insufficient stock for {sku.sku_code}: "
            f"requested {new_quantity}, available {_available_stock(sku)}."
        )

    cart.set_quantity(sku.id, new_quantity)
    return sku


def update_quantity(cart: Cart, sku_id, quantity: int) -> SKU:
    """Set an absolute quantity for an SKU.

    A quantity of 0 removes the line. Raises ``ValueError`` on invalid SKU,
    negative quantity, or insufficient stock.
    """
    quantity = _validate_quantity(quantity, allow_zero=True)
    sku = _get_active_sku(sku_id)

    if quantity == 0:
        cart.remove(sku.id)
        return sku

    if quantity > _available_stock(sku):
        raise ValueError(
            f"Insufficient stock for {sku.sku_code}: "
            f"requested {quantity}, available {_available_stock(sku)}."
        )

    cart.set_quantity(sku.id, quantity)
    return sku


def remove_from_cart(cart: Cart, sku_id) -> None:
    """Remove an SKU line from the cart (no-op if absent)."""
    cart.remove(sku_id)


def calculate_total(cart: Cart) -> Decimal:
    """Sum of every line subtotal at live SKU prices."""
    return sum((item.subtotal for item in cart), Decimal("0.00"))


def _validate_quantity(quantity, allow_zero: bool = False) -> int:
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        raise ValueError("Quantity must be an integer.")

    if quantity < 0 or (quantity == 0 and not allow_zero):
        raise ValueError("Quantity must be a positive integer.")

    return quantity
