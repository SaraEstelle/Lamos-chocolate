"""
apps/b2b/forms.py
=================
Forms for the public B2B funnel (quote / bulk-order requests).

- "website" is a hidden HONEYPOT: real users never see it, bots fill it.
- "wants_marketing" is an OPTIONAL, unchecked-by-default opt-in (nLPD). The
  request itself relies on legitimate interest, so consent is NOT required.
"""

from django import forms
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Customer
from apps.b2b.models import B2BRequest, CustomizationRequest
from apps.common.constants import (
    B2BAccountStatusChoices,
    B2BSegmentChoices,
    CustomerTypeChoices,
)
from apps.shop.models import SKU


class B2BRequestForm(forms.ModelForm):
    """Public form for a professional to request a quote / bulk order."""

    website = forms.CharField(  # honeypot, not a model field
        required=False,
        widget=forms.TextInput(
            attrs={
                "tabindex": "-1",
                "autocomplete": "off",
                "class": "d-none",
                "aria-hidden": "true",
            }
        ),
        label="",
    )
    wants_marketing = forms.BooleanField(
        required=False,
        initial=False,
        label=_("I agree to receive commercial offers from Lamos Chocolate"),
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = B2BRequest
        fields = (
            "company_name",
            "contact_name",
            "contact_email",
            "contact_phone",
            "sector",
            "estimated_qty",
            "occasion",
            "message",
        )
        widgets = {
            "company_name": forms.TextInput(attrs={"class": "form-control"}),
            "contact_name": forms.TextInput(attrs={"class": "form-control"}),
            "contact_email": forms.EmailInput(attrs={"class": "form-control"}),
            "contact_phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+41 (XX) XXX XX XX"}
            ),
            "sector": forms.TextInput(attrs={"class": "form-control"}),
            "estimated_qty": forms.NumberInput(
                attrs={"class": "form-control", "min": 1}
            ),
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


class ConfiguratorForm(forms.ModelForm):
    """4-axis personalisation form (logo / inner / outer packaging / grammage)."""

    class Meta:
        model = CustomizationRequest
        fields = (
            "sku",
            "logo_engraved",
            "inner_packaging",
            "outer_packaging",
            "grammage",
            "quantity",
        )
        widgets = {
            "sku": forms.Select(attrs={"class": "form-select"}),
            "logo_engraved": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "inner_packaging": forms.TextInput(attrs={"class": "form-control"}),
            "outer_packaging": forms.TextInput(attrs={"class": "form-control"}),
            "grammage": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only B2B-available SKUs can be configured.
        self.fields["sku"].queryset = SKU.objects.filter(
            is_active=True,
            b2b_info__is_b2b_available=True,
        )

    def clean_quantity(self):
        qty = self.cleaned_data.get("quantity")
        if qty is not None and qty < 1:
            raise forms.ValidationError(_("Quantity must be at least 1."))
        return qty


class B2BRegisterForm(forms.Form):
    """Self-service B2B registration. Creates a pending pro account."""

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    company_name = forms.CharField(max_length=200)
    sector = forms.ChoiceField(choices=B2BSegmentChoices.choices)
    phone = forms.CharField(max_length=20, required=False)
    password = forms.CharField(min_length=12, widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)
    preferred_language = forms.ChoiceField(
        choices=[
            ("fr", "Français"),
            ("en", "English"),
            ("de-ch", "Deutsch (Schweiz)"),
            ("it-ch", "Italiano (Svizzera)"),
        ],
        initial="en",
        label=_("Preferred language"),
    )
    accept_terms = forms.BooleanField(required=True)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if Customer.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_password(self):
        p = self.cleaned_data.get("password", "")
        checks = [
            any(c.isupper() for c in p),
            any(c.islower() for c in p),
            any(c.isdigit() for c in p),
            any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in p),
        ]
        if not all(checks):
            raise forms.ValidationError(
                "Password must contain uppercase, lowercase, digit and special char."
            )
        return p

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("password_confirm"):
            raise forms.ValidationError("The two passwords do not match.")
        return cleaned

    @transaction.atomic
    def save(self):
        """Create the Customer (pro, inactive portal) + a PENDING B2BAccount."""
        data = self.cleaned_data
        customer = Customer(
            email=data["email"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone=data.get("phone", ""),
            company_name=data["company_name"],
            preferred_language=data["preferred_language"],
            is_b2b=True,
            customer_type=CustomerTypeChoices.B2B_DISTRIBUTOR,
        )
        customer.set_password(data["password"])
        customer.save()

        from apps.accounts.models import B2BAccount

        account = B2BAccount.objects.create(
            customer=customer,
            company_name=data["company_name"],
            segment=data["sector"],
            status=B2BAccountStatusChoices.PENDING,
        )
        return customer, account
