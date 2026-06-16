"""
apps/customer_area/selectors.py
===============================
Read-only query helpers for the customer area.

These functions encapsulate ORM queries so views stay thin and queries
can be reused and tested in isolation. They always scope data to a given
customer (a customer must never see another customer's orders).
"""

from apps.checkout.models import Order


def get_customer_orders(customer):
    """
    Return all orders for a customer, most recent first.

    Uses select_related/prefetch_related to avoid N+1 queries when the
    template iterates over items.
    """
    return (
        Order.objects
        .filter(customer=customer)
        .select_related("shipping_zone", "payment")
        .prefetch_related("items__sku")
        .order_by("-created_at")
    )


def get_customer_order_or_none(customer, order_id):
    """
    Return a single order belonging to the customer, or None.

    Scoping by customer is a security measure: even if someone guesses an
    order id, they can only access their own orders.
    """
    return (
        Order.objects
        .filter(customer=customer, id=order_id)
        .select_related("shipping_zone", "payment")
        .prefetch_related("items__sku__product")
        .first()
    )


def get_customer_dashboard_stats(customer):
    """
    Return small aggregates for the dashboard header.

    Returns a dict: total number of orders and number of pending orders.
    """
    orders = Order.objects.filter(customer=customer)
    return {
        "total_orders": orders.count(),
        "pending_orders": orders.filter(status="pending").count(),
    }
def get_customer_addresses(customer):
    """Return all saved addresses for a customer (default first)."""
    from apps.customer_area.models import CustomerAddress
    return CustomerAddress.objects.filter(customer=customer)


def get_default_address(customer):
    """Return the customer's default address, or None."""
    from apps.customer_area.models import CustomerAddress
    return (
        CustomerAddress.objects
        .filter(customer=customer, is_default=True)
        .first()
    )


def get_filtered_customer_orders(customer, status=None):
    """
    Return the customer's orders, optionally filtered by status.

    Reuses the base scoped query and adds an optional status filter.
    """
    from apps.checkout.models import Order
    qs = (
        Order.objects
        .filter(customer=customer)
        .select_related("shipping_zone", "payment")
        .prefetch_related("items__sku")
        .order_by("-created_at")
    )
    if status:
        qs = qs.filter(status=status)
    return qs