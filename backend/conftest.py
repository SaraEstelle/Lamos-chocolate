"""Shared pytest fixtures for the Lamos Chocolate test suite.

Import paths are deliberately explicit (catalog models live in ``apps.shop``,
auth models in ``apps.accounts``/``apps.backoffice``, orders in
``apps.checkout``) — the project does NOT expose them all from a single module.
"""

import pytest


@pytest.fixture
def sample_category(db):
    """A single catalog category."""
    from apps.shop.models import Category

    return Category.objects.create(name_fr="Test", name_en="Test", slug="test-category")


@pytest.fixture
def sample_shipping_zone(db):
    """Switzerland zone — 2-day delivery delay (used by forecasting tests)."""
    from apps.shop.models import ShippingZone

    return ShippingZone.objects.create(
        zone_name="Switzerland", countries=["CH"], delay_days=2, cost="8.90"
    )


@pytest.fixture
def sample_product(db, sample_category):
    """A product with one in-stock SKU.

    Returns a ``(product, sku, stock)`` tuple. The SKU has
    ``production_delay_days=7`` and ``batch_size=50``, and the stock starts at
    50 units — the reference values used across the forecasting test cases.
    """
    from apps.shop.models import SKU, Product, Stock

    product = Product.objects.create(
        slug="test-pistachio",
        name_fr="Test Pistache",
        name_en="Test Pistachio",
        category=sample_category,
        is_active=True,
    )
    sku = SKU.objects.create(
        product=product,
        sku_code="TST-PIK-100",
        format="Bar 100g",
        price="12.90",
        currency="EUR",
        production_delay_days=7,
        batch_size=50,
    )
    stock = Stock.objects.create(sku=sku, quantity=50, threshold_alert=5)
    return product, sku, stock


@pytest.fixture
def sample_customer(db):
    """An active customer with a known password."""
    from apps.accounts.models import Customer

    customer = Customer(
        first_name="Marie",
        last_name="Test",
        email="marie.test@example.com",
        language_pref="fr",
    )
    customer.set_password("testpassword123")
    customer.save()
    return customer


@pytest.fixture
def sample_admin(db):
    """A superadmin backoffice user with a known password."""
    from apps.backoffice.models import AdminUser

    admin = AdminUser(
        email="admin@lamos-eu.com",
        first_name="Sara",
        last_name="Rebati",
        role="superadmin",
    )
    admin.set_password("adminpassword123")
    admin.save()
    return admin
