"""Unit tests for shop models: Stock behaviour and ShippingZone lookup."""

import pytest


class TestStockModel:
    def test_decrement_success(self, db, sample_product):
        _, _, stock = sample_product
        initial_qty = stock.quantity
        stock.decrement(5)
        stock.refresh_from_db()
        assert stock.quantity == initial_qty - 5

    def test_decrement_insufficient_stock_raises(self, db, sample_product):
        _, _, stock = sample_product
        stock.quantity = 2
        stock.save()
        with pytest.raises(ValueError, match="Insufficient stock"):
            stock.decrement(5)

    def test_decrement_exact_quantity_to_zero(self, db, sample_product):
        _, _, stock = sample_product
        stock.quantity = 5
        stock.save()
        stock.decrement(5)
        stock.refresh_from_db()
        assert stock.quantity == 0

    def test_increment(self, db, sample_product):
        _, _, stock = sample_product
        initial_qty = stock.quantity
        stock.increment(10)
        stock.refresh_from_db()
        assert stock.quantity == initial_qty + 10

    def test_is_low_when_at_threshold(self, db, sample_product):
        _, _, stock = sample_product
        stock.quantity = 5
        stock.threshold_alert = 5
        assert stock.is_low is True

    def test_is_low_when_below_threshold(self, db, sample_product):
        _, _, stock = sample_product
        stock.quantity = 3
        stock.threshold_alert = 5
        assert stock.is_low is True

    def test_is_low_when_above_threshold(self, db, sample_product):
        _, _, stock = sample_product
        stock.quantity = 10
        stock.threshold_alert = 5
        assert stock.is_low is False


class TestShippingZone:
    def test_get_zone_for_country_found(self, db, sample_shipping_zone):
        from apps.shop.models import ShippingZone

        zone = ShippingZone.get_zone_for_country("CH")
        assert zone is not None
        assert zone.zone_name == "Switzerland"
        assert zone.delay_days == 2

    def test_get_zone_for_country_not_found(self, db, sample_shipping_zone):
        from apps.shop.models import ShippingZone

        assert ShippingZone.get_zone_for_country("XX") is None


class TestProductImage:
    def test_primary_image_url_returns_primary(self, db, sample_product):
        from apps.shop.models import ProductImage

        product, _, _ = sample_product
        ProductImage.objects.create(
            product=product, image_url="/secondary.webp", is_primary=False
        )
        ProductImage.objects.create(
            product=product, image_url="/primary.webp", is_primary=True
        )
        assert product.primary_image_url == "/primary.webp"

    def test_primary_image_url_falls_back_to_first(self, db, sample_product):
        from apps.shop.models import ProductImage

        product, _, _ = sample_product
        ProductImage.objects.create(
            product=product, image_url="/only.webp", is_primary=False
        )
        assert product.primary_image_url == "/only.webp"

    def test_primary_image_url_empty_when_no_images(self, db, sample_product):
        product, _, _ = sample_product
        assert product.primary_image_url == ""

    def test_ordering_puts_primary_first(self, db, sample_product):
        from apps.shop.models import ProductImage

        product, _, _ = sample_product
        ProductImage.objects.create(
            product=product, image_url="/secondary.webp", is_primary=False
        )
        primary = ProductImage.objects.create(
            product=product, image_url="/primary.webp", is_primary=True
        )
        assert product.images.first() == primary
