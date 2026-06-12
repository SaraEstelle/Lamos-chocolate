"""Unit tests for PasswordResetToken validity logic."""

from datetime import timedelta

from django.utils import timezone


class TestPasswordResetToken:
    def test_is_valid_fresh_token(self, db, sample_customer):
        from apps.accounts.models import PasswordResetToken

        token = PasswordResetToken.objects.create(
            customer=sample_customer,
            token="valid-token-abc",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        assert token.is_valid is True

    def test_is_valid_expired_token(self, db, sample_customer):
        from apps.accounts.models import PasswordResetToken

        token = PasswordResetToken.objects.create(
            customer=sample_customer,
            token="expired-token-xyz",
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        assert token.is_valid is False

    def test_is_valid_used_token(self, db, sample_customer):
        from apps.accounts.models import PasswordResetToken

        token = PasswordResetToken.objects.create(
            customer=sample_customer,
            token="used-token-def",
            expires_at=timezone.now() + timedelta(hours=1),
            used=True,
        )
        assert token.is_valid is False

    def test_create_for_customer_returns_valid_token(self, db, sample_customer):
        from apps.accounts.models import PasswordResetToken

        token = PasswordResetToken.create_for_customer(sample_customer)
        assert token.customer == sample_customer
        assert token.token  # a non-empty secret was generated
        assert token.is_valid is True
