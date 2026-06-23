"""
Delete B2B requests older than the retention period (nLPD data minimisation).

Usage:
    python manage.py purge_old_b2b_requests --years 3
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.b2b.models import B2BRequest


class Command(BaseCommand):
    help = "Delete B2B requests older than the retention period (default 3 years)."

    def add_arguments(self, parser):
        parser.add_argument("--years", type=int, default=3)

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=365 * options["years"])
        qs = B2BRequest.objects.filter(created_at__lt=cutoff)
        count = qs.count()
        qs.delete()
        self.stdout.write(self.style.SUCCESS(
            f"Deleted {count} B2B requests older than {options['years']} years."
        ))
