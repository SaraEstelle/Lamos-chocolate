"""
apps/backoffice/selectors.py
============================
Read-only queries for the staff backoffice (B2B account moderation).

Kept separate from views so the querysets can be tested in isolation and
reused (dashboard KPI + list page share the same source of truth).
"""

from apps.accounts.models import B2BAccount
from apps.common.constants import B2BAccountStatusChoices


def get_pending_b2b_accounts():
    """
    Return B2B accounts awaiting a staff decision, oldest first.

    'pending' = self-registered pro who submitted the form and now waits for
    validation (created by b2b:register). We select_related the customer to
    avoid one extra query per row in the template (N+1 protection).
    """
    return (
        B2BAccount.objects.filter(status=B2BAccountStatusChoices.PENDING)
        .select_related("customer")
        .order_by("created_at")  # first-come, first-served
    )


def count_pending_b2b_accounts():
    """Small helper for the dashboard KPI card."""
    return B2BAccount.objects.filter(status=B2BAccountStatusChoices.PENDING).count()
