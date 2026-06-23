"""
apps/b2b/forms.py
=================
Forms for the public B2B funnel (quote / bulk-order requests).

- "website" is a hidden HONEYPOT: real users never see it, bots fill it.
- "wants_marketing" is an OPTIONAL, unchecked-by-default opt-in (nLPD). The
  request itself relies on legitimate interest, so consent is NOT required.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.b2b.models import B2BRequest


class B2BRequestForm(forms.ModelForm):
    """Public form for a professional to request a quote / bulk order."""

    website = forms.CharField(  # honeypot, not a model field
        required=False,
        widget=forms.TextInput(attrs={
            "tabindex": "-1", "autocomplete": "off",
            "class": "d-none", "aria-hidden": "true",
        }),
        label="",
    )
    wants_marketing = forms.BooleanField(
        required=False, initial=False,
        label=_("I agree to receive commercial offers from Lamos Chocolate"),
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = B2BRequest
        fields = (
            "company_name", "contact_name", "contact_email", "contact_phone",
            "sector", "estimated_qty", "occasion", "message",
        )
        widgets = {
            "company_name": forms.TextInput(attrs={"class": "form-control"}),
            "contact_name": forms.TextInput(attrs={"class": "form-control"}),
            "contact_email": forms.EmailInput(attrs={"class": "form-control"}),
            "contact_phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "+41 (XX) XXX XX XX"}),
            "sector": forms.TextInput(attrs={"class": "form-control"}),
            "estimated_qty": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "occasion": forms.TextInput(attrs={"class": "form-control"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def is_bot(self):
        """Return True if the honeypot was filled (likely a bot)."""
        return bool(self.cleaned_data.get("website"))

    def clean_estimated_qty(self):
        qty = self.cleaned_data.get("estimated_qty")
        if qty is not None and qty < 1:
            raise forms.ValidationError(_("Quantity must be at least 1."))
        return qty