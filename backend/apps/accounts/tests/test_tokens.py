"""
apps/accounts/tests/test_tokens.py
===================================
Tests for password reset tokens.

Tests:
- generate_reset_token(): random unique token
- create_reset_token(): creation with expiration
- verify_reset_token(): validation (expired, used)
- mark_token_as_used(): one-time use
"""

import pytest
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import Customer, PasswordResetToken
from apps.accounts.tokens import (
    generate_reset_token, create_reset_token, verify_reset_token, mark_token_as_used
)


@pytest.mark.django_db
class TestTokens:
    """Tests for tokens."""

    def setup_method(self):
        """Create a customer."""
        self.customer = Customer.objects.create_user(
            email='john@example.com',
            password='SecurePass123!'
        )

    def test_generate_reset_token_format(self):
        """Generated token has correct format."""
        token = generate_reset_token()
        assert isinstance(token, str)
        assert len(token) > 30

    def test_generate_reset_token_unique(self):
        """Generated tokens are unique."""
        token1 = generate_reset_token()
        token2 = generate_reset_token()
        assert token1 != token2

    def test_create_reset_token(self):
        """Create a token."""
        token = create_reset_token(self.customer)
        assert token.customer == self.customer
        assert token.is_used == False
        assert token.expires_at > timezone.now()

    def test_verify_reset_token_valid(self):
        """Verify a valid token."""
        token = create_reset_token(self.customer)
        verified = verify_reset_token(token.token)
        assert verified is not None
        assert verified.customer == self.customer

    def test_verify_reset_token_invalid(self):
        """Verify an invalid token."""
        verified = verify_reset_token('invalid-token-xyz')
        assert verified is None

    def test_verify_reset_token_expired(self):
        """Verify an expired token."""
        token = create_reset_token(self.customer)
        token.expires_at = timezone.now() - timedelta(hours=1)
        token.save()

        verified = verify_reset_token(token.token)
        assert verified is None

    def test_verify_reset_token_used(self):
        """Verify an already used token."""
        token = create_reset_token(self.customer)
        mark_token_as_used(token)

        verified = verify_reset_token(token.token)
        assert verified is None

    def test_mark_token_as_used(self):
        """Mark a token as used."""
        token = create_reset_token(self.customer)
        assert token.is_used == False

        mark_token_as_used(token)
        token.refresh_from_db()
        assert token.is_used == True