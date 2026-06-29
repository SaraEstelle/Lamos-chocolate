"""
apps/checkout/forms.py
======================
Forms for the checkout flow.
"""

from django import forms
from django.utils.translation import gettext_lazy as _


class ShippingForm(forms.Form):
    """Destination address collected at checkout.

    Field names mirror the ``shipping_*`` snapshot columns on ``Order`` (minus
    the prefix), so :meth:`as_shipping_dict` plugs straight into
    ``create_paid_order(shipping=...)``.
    """

    first_name = forms.CharField(
        label=_("First name"),
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label=_("Last name"),
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    address1 = forms.CharField(
        label=_("Address"),
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    address2 = forms.CharField(
        label=_("Address (complement)"),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    city = forms.CharField(
        label=_("City"),
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    postal_code = forms.CharField(
        label=_("Postal code"),
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    country = forms.CharField(
        label=_("Country"),
        max_length=2,
        help_text=_("Two-letter country code (e.g. CH, FR)."),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    def clean_country(self):
        return self.cleaned_data["country"].upper()

    def as_shipping_dict(self):
        """Return the cleaned fields shaped for ``create_paid_order``."""
        return {
            "first_name": self.cleaned_data["first_name"],
            "last_name": self.cleaned_data["last_name"],
            "address1": self.cleaned_data["address1"],
            "address2": self.cleaned_data.get("address2", ""),
            "city": self.cleaned_data["city"],
            "postal_code": self.cleaned_data["postal_code"],
            "country": self.cleaned_data["country"],
        }
