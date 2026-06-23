"""
apps/b2b/selectors.py
=====================
Read-only queries for the B2B app (never write).
"""

from datetime import timedelta

from django.utils import timezone

from apps.b2b.models import B2BRequest


def has_recent_duplicate(*, contact_email, company_name, within_minutes=10):
    """Return True if an identical request was just submitted (double-submit guard)."""
    since = timezone.now() - timedelta(minutes=within_minutes)
    return (
        B2BRequest.objects.filter(
            contact_email__iexact=contact_email,
            company_name__iexact=company_name,
            created_at__gte=since,
        ).exists()
    )