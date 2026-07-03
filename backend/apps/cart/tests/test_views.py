"""Integration tests for the cart HTTP endpoints.

Endpoints answer in two modes: a plain form POST is redirected back to the cart
page (PRG), while an AJAX request (``X-Requested-With``) gets a JSON payload.
"""

from django.urls import reverse

AJAX = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


class TestAddItemViewForm:
    def test_add_redirects_to_cart(self, db, client, sample_product):
        _, sku, _ = sample_product
        response = client.post(reverse("cart:add"), {"sku_id": sku.id, "quantity": 2})
        assert response.status_code == 302
        assert response.url == reverse("cart:view")

    def test_add_persists_item(self, db, client, sample_product):
        _, sku, _ = sample_product
        client.post(reverse("cart:add"), {"sku_id": sku.id, "quantity": 2})
        assert client.session["cart"] == {str(sku.id): {"quantity": 2}}

    def test_add_invalid_sku_redirects(self, db, client):
        response = client.post(reverse("cart:add"), {"sku_id": 999999, "quantity": 1})
        assert response.status_code == 302

    def test_get_not_allowed(self, db, client):
        assert client.get(reverse("cart:add")).status_code == 405


class TestAddItemViewAjax:
    def test_add_returns_serialized_cart(self, db, client, sample_product):
        _, sku, _ = sample_product
        response = client.post(
            reverse("cart:add"), {"sku_id": sku.id, "quantity": 2}, **AJAX
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 2
        assert data["total_price"] == "25.80"
        assert data["items"][0]["sku_code"] == sku.sku_code

    def test_add_invalid_sku_returns_400(self, db, client):
        response = client.post(
            reverse("cart:add"), {"sku_id": 999999, "quantity": 1}, **AJAX
        )
        assert response.status_code == 400
        assert "error" in response.json()

    def test_add_beyond_stock_returns_400(self, db, client, sample_product):
        _, sku, _ = sample_product
        response = client.post(
            reverse("cart:add"), {"sku_id": sku.id, "quantity": 99}, **AJAX
        )
        assert response.status_code == 400
        assert "Insufficient stock" in response.json()["error"]


class TestRemoveItemView:
    def test_remove_clears_line_ajax(self, db, client, sample_product):
        _, sku, _ = sample_product
        client.post(reverse("cart:add"), {"sku_id": sku.id, "quantity": 2})
        response = client.post(reverse("cart:remove"), {"sku_id": sku.id}, **AJAX)
        assert response.status_code == 200
        assert response.json()["is_empty"] is True

    def test_remove_redirects_for_form(self, db, client, sample_product):
        _, sku, _ = sample_product
        client.post(reverse("cart:add"), {"sku_id": sku.id, "quantity": 2})
        response = client.post(reverse("cart:remove"), {"sku_id": sku.id})
        assert response.status_code == 302
        assert response.url == reverse("cart:view")


class TestCartView:
    def test_cart_page_renders(self, db, client, sample_product):
        _, sku, _ = sample_product
        client.post(reverse("cart:add"), {"sku_id": sku.id, "quantity": 1})
        response = client.get(reverse("cart:view"))
        assert response.status_code == 200
        assert sku.product.name_fr.encode() in response.content
