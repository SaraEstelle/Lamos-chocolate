"""
apps/shop/forms.py
==================
Forms for the shop catalog.
"""

from django import forms
from django.utils.translation import gettext_lazy as _


class SearchForm(forms.Form):
    """Catalog search form (single free-text query)."""

    q = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(
            attrs={"placeholder": _("Search products..."), "type": "search"}
        ),
    )
