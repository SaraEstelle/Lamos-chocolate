"""
apps/backoffice/services.py
===========================
Write operations for the staff backoffice (B2B account moderation).

Design choices:
- We NEVER hard-delete a refused account. Swiss law (CO art. 958f) requires
  retaining business records; refusal only DEACTIVATES the account. This also
  keeps an audit trail of who applied.
- Activation is idempotent-friendly: re-activating an already active account
  is harmless.
"""

from django.utils import timezone

from apps.common.constants import B2BAccountStatusChoices


def activate_b2b_account(account):
    """
    Grant portal access to a pending pro account.

    Sets status to ACTIVE and stamps onboarded_at (used by the cockpit funnel
    to measure time-to-activation). Returns the updated account.
    """
    account.status = B2BAccountStatusChoices.ACTIVE
    if account.onboarded_at is None:
        account.onboarded_at = timezone.now()
    account.save(update_fields=["status", "onboarded_at"])
    return account


def reject_b2b_account(account):
    """
    Refuse / deactivate a pro account WITHOUT deleting it.

    We reuse the DORMANT status to mean 'access not granted / deactivated'.
    No hard delete: Swiss accounting retention (CO art. 958f) + audit trail.

    NOTE: there is no dedicated 'refused' status in B2BAccountStatusChoices
    today. If you later want to distinguish 'refused' from 'dormant', add a
    REFUSED choice to the enum (that will create a no-op migration). For now,
    DORMANT is the safe, migration-free option.
    """
    account.status = B2BAccountStatusChoices.DORMANT
    account.save(update_fields=["status"])
    return account
