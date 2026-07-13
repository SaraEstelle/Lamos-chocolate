"""
apps/accounts/tests/test_access_view.py
=======================================
Regression tests for the B2C sliding auth page (accounts:access).

Why this file exists
--------------------
The sign-up form used to POST WITHOUT `preferred_language` (the field was never
rendered in access.html). RegisterForm is a ModelForm on Customer, where
preferred_language has no blank=True -> the field is required -> is_valid() was
always False, and the error was not displayed anywhere. The user experienced a
page that silently reloaded.

These tests lock that behaviour down for good.
"""

import pytest
from django.urls import reverse

from apps.accounts.models import Customer

# Valid B2C payload: exactly what the fixed access.html now sends.
VALID_PAYLOAD = {
    "form_type": "register",          # tells access_view() which branch to run
    "first_name": "Sara",
    "last_name": "Estelle",
    "email": "sara.b2c@lamos.ch",
    "preferred_language": "fr",       # <-- the field that used to be missing
    "password": "Chocolat2026!",
    "password_confirm": "Chocolat2026!",
    "gdpr": "on",                     # nLPD consent checkbox
}


@pytest.mark.django_db
def test_b2c_signup_creates_customer(client):
    """A complete, valid payload must create an active B2C Customer."""
    response = client.post(reverse("accounts:access"), data=VALID_PAYLOAD)

    # The view redirects back to the sign-in side of the same page.
    assert response.status_code == 302

    customer = Customer.objects.get(email="sara.b2c@lamos.ch")
    assert customer.is_b2b is False               # this is the B2C funnel
    assert customer.preferred_language == "fr"
    assert customer.check_password("Chocolat2026!")  # password is hashed, not stored raw


@pytest.mark.django_db
def test_b2c_signup_stores_nlpd_consent(client):
    """Swiss nLPD: consent must be stored WITH a timestamp (proof of consent)."""
    client.post(reverse("accounts:access"), data=VALID_PAYLOAD)

    customer = Customer.objects.get(email="sara.b2c@lamos.ch")
    assert customer.consent_nlpd is True
    assert customer.consent_nlpd_at is not None


@pytest.mark.django_db
def test_b2c_signup_rejected_without_gdpr_consent(client):
    """No consent -> no account. Hard requirement under nLPD/GDPR."""
    payload = {**VALID_PAYLOAD}
    payload.pop("gdpr")

    response = client.post(reverse("accounts:access"), data=payload)

    assert response.status_code == 200            # re-rendered, not redirected
    assert not Customer.objects.filter(email="sara.b2c@lamos.ch").exists()


@pytest.mark.django_db
def test_signup_form_renders_preferred_language_field(client):
    """
    THE regression guard.

    If someone removes the <select name="preferred_language"> from access.html
    again, sign-up breaks silently. This test fails loudly instead.
    """
    response = client.get(reverse("accounts:access") + "?mode=register")

    assert response.status_code == 200
    html = response.content.decode()
    assert 'name="preferred_language"' in html