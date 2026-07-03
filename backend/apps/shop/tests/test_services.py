"""Tests for shop services (per-zone delivery estimates)."""

from apps.shop import services


class TestDeliveryEstimates:
    def test_in_stock_uses_zone_delay(self, sample_product, sample_shipping_zone):
        # sample_product stock starts at 50 units.
        _, sku, _ = sample_product
        estimates = services.get_delivery_estimates(sku, quantity=1)
        assert len(estimates) == 1
        assert estimates[0]["zone"] == sample_shipping_zone
        assert estimates[0]["days"] == sample_shipping_zone.delay_days  # 2

    def test_deficit_adds_production_days(self, sample_product, sample_shipping_zone):
        _, sku, stock = sample_product
        stock.quantity = 0
        stock.save()
        # deficit 1 → ceil(1/50)=1 batch × 7 production days + 2 shipping = 9
        estimates = services.get_delivery_estimates(sku, quantity=1)
        assert estimates[0]["days"] == 7 + 2

    def test_one_entry_per_zone(self, sample_product, sample_shipping_zone):
        from apps.shop.models import ShippingZone

        ShippingZone.objects.create(
            zone_name="France", countries=["FR"], delay_days=3, cost="6.90"
        )
        _, sku, _ = sample_product
        estimates = services.get_delivery_estimates(sku)
        assert len(estimates) == 2

    def test_no_zones_returns_empty(self, sample_product):
        _, sku, _ = sample_product
        assert services.get_delivery_estimates(sku) == []
