import pytest
from django.urls import reverse

@pytest.mark.integration
class TestAddresses:
    def test_addresses_requires_login(self, client, db):
        resp = client.get(reverse("customer_area:addresses"))
        assert resp.status_code == 302

    def test_create_address(self, client, customer_factory):
        customer = customer_factory()
        client.force_login(customer)
        resp = client.post(reverse("customer_area:address_create"), data={
            "label": "Home",
            "full_name": "Test User",
            "line1": "1 rue du Test",
            "city": "Genève",
            "postal_code": "1200",
            "canton": "GE",
            "country": "Suisse",
            "is_default": "on",
        })
        assert resp.status_code == 302
        from apps.customer_area.models import CustomerAddress
        assert CustomerAddress.objects.filter(customer=customer).count() == 1
        # The default address denormalizes canton/npa onto the customer.
        customer.refresh_from_db()
        assert customer.canton == "GE"
        assert customer.npa == "1200"

    def test_only_one_default_address(self, client, customer_factory):
        customer = customer_factory()
        from apps.customer_area.models import CustomerAddress
        a1 = CustomerAddress.objects.create(
            customer=customer, full_name="A", line1="1", city="X",
            postal_code="1", country="CH", is_default=True,
        )
        a2 = CustomerAddress.objects.create(
            customer=customer, full_name="B", line1="2", city="Y",
            postal_code="2", country="CH", is_default=True,
        )
        a1.refresh_from_db()
        # Only the most recent default should remain default
        assert a2.is_default is True
        assert a1.is_default is False

    def test_cannot_edit_another_customers_address(self, client, customer_factory):
        alice = customer_factory(email="al@test.com")
        bob = customer_factory(email="bo@test.com")
        from apps.customer_area.models import CustomerAddress
        bob_addr = CustomerAddress.objects.create(
            customer=bob, full_name="Bob", line1="1", city="X",
            postal_code="1", country="CH",
        )
        client.force_login(alice)
        resp = client.get(reverse("customer_area:address_edit", args=[bob_addr.id]))
        assert resp.status_code == 404