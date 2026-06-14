"""
apps/accounts/tokens.py
=======================
Secure tokens for password reset.

Responsibilities:
1. generate_reset_token() — Generate a random token
2. create_reset_token() — Create a PasswordResetToken in DB
3. verify_reset_token() — Verify that a token is valid
4. mark_token_as_used() — Mark as used (one-time use)

Security:
- Tokens are random (secrets.token_urlsafe)
- Tokens are unique in DB
- Tokens expire in 1h
- Tokens one-time use (can only be used once)
- No revelation if token exists or not
"""

import secrets
from datetime import timedelta
from django.utils import timezone
from apps.accounts.models import PasswordResetToken, Customer


def generate_reset_token() -> str:
    """
    Generate a cryptographically secure random token.

    Uses secrets.token_urlsafe() for cryptographic randomness.
    Return: ~43 character string, URL-safe

    Example: "Wj7vB-8cXq9kL2mN5pR_tY4aB6cD3eF0gH-jKlMnO"
    """
    # token_urlsafe(32) generates 43 characters
    # Sufficient for strong security
    return secrets.token_urlsafe(32)


def create_reset_token(customer: Customer) -> PasswordResetToken:
    """
    Create a PasswordResetToken for a customer.

    Process:
    1. Generate a unique token
    2. Set expires_at = now + 1h
    3. Save to DB

    Args:
        customer (Customer): The customer requesting password reset

    Return:
        PasswordResetToken: The created token object

    Example:
        token = create_reset_token(customer)
        # token.token = "Wj7vB-8cXq9kL..."
        # token.expires_at = 2026-06-13 15:42 (1h from now)
    """
    # Generate a unique token
    token_string = generate_reset_token()

    # Set expiration (1 hour — security requirement)
    now = timezone.now()
    expires_at = now + timedelta(hours=1)

    # Create in DB
    token = PasswordResetToken.objects.create(
        customer=customer,
        token=token_string,
        expires_at=expires_at,
        is_used=False
    )

    return token


def verify_reset_token(token_string: str) -> PasswordResetToken | None:
    """
    Verify that a reset token is valid.

    Verifies 3 conditions:
    1. Token exists in DB
    2. Token is not expired
    3. Token has not been used

    Args:
        token_string (str): The token to verify

    Return:
        PasswordResetToken if valid, None otherwise

    Example:
        token = verify_reset_token("Wj7vB-8cXq9kL...")
        if token:
            print("Token is valid, can reset password")
        else:
            print("Token is invalid or expired")
    """
    try:
        # 1. Find the token in DB
        token_obj = PasswordResetToken.objects.get(token=token_string)
    except PasswordResetToken.DoesNotExist:
        # Token does not exist
        return None

    # 2. Check that token is not expired
    if not token_obj.is_valid():
        return None

    # 3. Check that token has not been used
    if token_obj.is_used:
        return None

    # ✅ Token is valid
    return token_obj


def mark_token_as_used(token: PasswordResetToken) -> None:
    """
    Mark a token as used (one-time use).

    Once used, the token cannot be reused.
    This is a security measure against brute force attacks.

    Args:
        token (PasswordResetToken): The token to mark

    Example:
        token = verify_reset_token("Wj7vB-8cXq9kL...")
        if token:
            # User has changed password
            mark_token_as_used(token)  # Mark as used
            # Now this token cannot be used again
    """
    # Mark as used
    token.is_used = True
    token.save()