"""
apps/main/forms.py
==================
Forms for the public main app.
"""

from django import forms
from django.utils.translation import gettext_lazy as _


class ContactForm(forms.Form):
    """Simple contact form (name, email, message)."""

    name = forms.CharField(
        max_length=100,
        label=_("Your name"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label=_("Your email"),
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    message = forms.CharField(
        label=_("Message"),
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 5}),
    )