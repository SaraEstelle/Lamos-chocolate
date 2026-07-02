"""
apps/backoffice/tests/test_b2b_accounts.py
==========================================
Staff validation of self-registered pro accounts.
"""

import pytest
from django.urls import reverse

from apps.accounts.models import B2BAccount, Customer
from apps.common.constants import (
    B2BAccountStatusChoices,
    CustomerTypeChoices,
)


def make_staff():
    """A staff user who can reach the backoffice."""
    return Customer.objects.create_user(
        email="staff@lamos.ch", password="StrongP@ss1!", is_staff=True,
    )


def make_pending_account(email="prospect@test.com"):
    """A self-registered pro waiting for validation."""
    customer = Customer.objects.create_user(
        email=email, password="StrongP@ss1!",
        customer_type=CustomerTypeChoices.B2B_DISTRIBUTOR,
    )
    return B2BAccount.objects.create(
        customer=customer, company_name="Prospect SA",
        status=B2BAccountStatusChoices.PENDING,
    )


@pytest.mark.django_db
class TestB2BAccountValidation:

    def test_list_requires_staff(self, client):
        """A non-staff user must not reach the validation page."""
        c = Customer.objects.create_user(
            email="b2c@test.com", password="StrongP@ss1!",
        )
        client.force_login(c)
        resp = client.get(reverse("backoffice:b2b_accounts"))
        assert resp.status_code in (302, 403)  # redirected to admin login / denied

    def test_staff_sees_pending_account(self, client):
        make_pending_account()
        client.force_login(make_staff())
        resp = client.get(reverse("backoffice:b2b_accounts"))
        assert resp.status_code == 200
        assert b"Prospect SA" in resp.content

    def test_activate_sets_active_and_onboarded(self, client):
        account = make_pending_account()
        client.force_login(make_staff())
        resp = client.post(
            reverse("backoffice:b2b_account_decision", args=[account.id]),
            {"decision": "activate"},
        )
        assert resp.status_code == 302
        account.refresh_from_db()
        assert account.status == B2BAccountStatusChoices.ACTIVE
        assert account.onboarded_at is not None

    def test_reject_deactivates_without_delete(self, client):
        account = make_pending_account()
        client.force_login(make_staff())
        resp = client.post(
            reverse("backoffice:b2b_account_decision", args=[account.id]),
            {"decision": "reject"},
        )
        assert resp.status_code == 302
        account.refresh_from_db()
        # No hard delete (Swiss retention): the record still exists.
        assert account.status == B2BAccountStatusChoices.DORMANT

    def test_decision_is_post_only(self, client):
        account = make_pending_account()
        client.force_login(make_staff())
        # A GET must NOT change state.
        resp = client.get(
            reverse("backoffice:b2b_account_decision", args=[account.id])
        )
        assert resp.status_code == 405  # Method Not Allowed
