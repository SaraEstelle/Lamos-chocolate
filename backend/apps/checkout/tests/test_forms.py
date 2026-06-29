"""Unit tests for the checkout shipping form (``ShippingForm``).

The form collects the destination address at checkout time. Its only job is to
validate the fields and expose them, via :meth:`as_shipping_dict`, in the exact
shape expected by ``create_paid_order(shipping=...)`` (keys without the
``shipping_`` prefix).
"""

from apps.checkout.forms import ShippingForm

VALID = {
    "first_name": "Marie",
    "last_name": "Test",
    "address1": "Rue du Test 1",
    "address2": "",
    "city": "Genève",
    "postal_code": "1200",
    "country": "ch",
}


class TestShippingForm:
    def test_valid_data(self):
        form = ShippingForm(data=VALID)
        assert form.is_valid(), form.errors

    def test_address2_is_optional(self):
        data = {**VALID}
        data.pop("address2")
        form = ShippingForm(data=data)
        assert form.is_valid(), form.errors

    def test_country_is_uppercased(self):
        form = ShippingForm(data=VALID)
        assert form.is_valid(), form.errors
        assert form.cleaned_data["country"] == "CH"

    def test_required_fields_missing(self):
        form = ShippingForm(data={})
        assert not form.is_valid()
        for field in ("first_name", "last_name", "address1", "city",
                      "postal_code", "country"):
            assert field in form.errors

    def test_as_shipping_dict_shape(self):
        form = ShippingForm(data=VALID)
        assert form.is_valid(), form.errors
        shipping = form.as_shipping_dict()
        assert shipping == {
            "first_name": "Marie",
            "last_name": "Test",
            "address1": "Rue du Test 1",
            "address2": "",
            "city": "Genève",
            "postal_code": "1200",
            "country": "CH",
        }
