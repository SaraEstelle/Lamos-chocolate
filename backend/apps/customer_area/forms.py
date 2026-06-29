"""
apps/customer_area/forms.py
===========================
Forms for the customer area.
"""

from django import forms

from apps.common.constants import SwissCantonChoices
from apps.customer_area.models import CustomerAddress


class AddressForm(forms.ModelForm):
    """Create or edit a saved shipping address."""

    # Mandatory on the form even though the model field is blank=True,
    # so existing rows / other code paths stay valid while new addresses
    # always capture a canton for the sales heatmap.
    canton = forms.ChoiceField(
        choices=[("", "— Sélectionnez un canton —")] + list(SwissCantonChoices.choices),
        required=True,
        label="Canton",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = CustomerAddress
        fields = (
            "label", "full_name", "line1", "line2",
            "city", "postal_code", "canton", "country", "is_default",
        )
        widgets = {
            "label": forms.TextInput(attrs={"class": "form-control"}),
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "line1": forms.TextInput(attrs={"class": "form-control"}),
            "line2": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.TextInput(attrs={"class": "form-control"}),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }