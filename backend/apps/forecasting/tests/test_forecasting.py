"""Forecasting tests — SKU.calculate_estimated_days().

Rule (see Technical documentation, forecasting section):
- stock >= order_quantity  -> shipping delay only
- stock <  order_quantity  -> ceil(deficit / batch_size) production batches
                              * production_delay_days, then + shipping delay

Reference SKU (from the ``sample_product`` fixture): production_delay_days=7,
batch_size=50, stock=50. Reference zone (``sample_shipping_zone``): delay_days=2.
"""


class TestSKUForecasting:
    def test_estimated_days_stock_sufficient(
        self, db, sample_product, sample_shipping_zone
    ):
        """Stock covers the order -> shipping delay only (2 days)."""
        _, sku, _ = sample_product
        # stock=50, order=10 -> sufficient -> zone delay = 2
        assert sku.calculate_estimated_days(10, sample_shipping_zone) == 2

    def test_estimated_days_stock_exactly_equal(
        self, db, sample_product, sample_shipping_zone
    ):
        """Boundary: stock == order is still 'sufficient' (>=)."""
        _, sku, _ = sample_product
        # stock=50, order=50 -> sufficient -> 2
        assert sku.calculate_estimated_days(50, sample_shipping_zone) == 2

    def test_estimated_days_stock_insufficient_one_batch(
        self, db, sample_product, sample_shipping_zone
    ):
        """Stock < order, deficit fits one batch -> 1*7 + 2 = 9 days."""
        _, sku, stock = sample_product
        stock.quantity = 5
        stock.save()
        # deficit=50, batches=ceil(50/50)=1, production=7, shipping=2 -> 9
        assert sku.calculate_estimated_days(55, sample_shipping_zone) == 9

    def test_estimated_days_zero_stock_one_batch(
        self, db, sample_product, sample_shipping_zone
    ):
        """Zero stock, order == batch_size -> full production of one batch."""
        _, sku, stock = sample_product
        stock.quantity = 0
        stock.save()
        # deficit=50, batches=1, 7 + 2 -> 9
        assert sku.calculate_estimated_days(50, sample_shipping_zone) == 9

    def test_estimated_days_deficit_just_over_one_batch(
        self, db, sample_product, sample_shipping_zone
    ):
        """Deficit one unit over a batch -> rounds up to 2 batches."""
        _, sku, stock = sample_product
        stock.quantity = 0
        stock.save()
        # deficit=51, batches=ceil(51/50)=2, production=14, shipping=2 -> 16
        assert sku.calculate_estimated_days(51, sample_shipping_zone) == 16

    def test_estimated_days_multiple_batches(
        self, db, sample_product, sample_shipping_zone
    ):
        """Large deficit spanning several batches."""
        _, sku, stock = sample_product
        stock.quantity = 0
        stock.save()
        # deficit=120, batches=ceil(120/50)=3, production=21, shipping=2 -> 23
        assert sku.calculate_estimated_days(120, sample_shipping_zone) == 23

    def test_estimated_days_uses_zone_delay(self, db, sample_product):
        """The shipping component comes from the given zone, not a constant."""
        from apps.shop.models import ShippingZone

        _, sku, _ = sample_product  # stock=50, sufficient
        eu_zone = ShippingZone.objects.create(
            zone_name="EU", countries=["DE", "AT"], delay_days=7, cost="12.00"
        )
        assert sku.calculate_estimated_days(10, eu_zone) == 7
