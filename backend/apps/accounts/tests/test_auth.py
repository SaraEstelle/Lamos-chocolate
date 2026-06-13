"""
apps/accounts/tests/test_auth.py
=================================
Tests for authentication services.

Tests:
- create_customer(): create customer
- send_welcome_email(): send email
- send_password_reset_email(): send link
- authenticate_customer(): verify credentials
"""

import pytest
from django.test import TestCase
from django.core import mail
from apps.accounts.models import Customer
from apps.accounts.services import (
    create_customer, authenticate_customer
)
from apps.accounts.tokens import create_reset_token


@pytest.mark.django_db
class TestCreateCustomer(TestCase):
    """Tests for customer creation."""

    def test_create_customer_success(self):
        """Create a customer successfully."""
        customer = create_customer(
            email='john@example.com',
            password='SecurePass123!',
            first_name='John',
            last_name='Doe'
        )
        assert customer.id is not None
        assert customer.email == 'john@example.com'
        assert customer.check_password('SecurePass123!')

    def test_create_customer_duplicate_email(self):
        """Create with email already in use."""
        create_customer(
            email='john@example.com',
            password='SecurePass123!',
            first_name='John',
            last_name='Doe'
        )

        with pytest.raises(ValueError):
            create_customer(
                email='john@example.com',
                password='DifferentPass123!',
                first_name='Jane',
                last_name='Smith'
            )

    def test_create_customer_sends_welcome_email(self):
        """Welcome email is sent."""
        customer = create_customer(
            email='john@example.com',
            password='SecurePass123!',
            first_name='John',
            last_name='Doe'
        )

        assert len(mail.outbox) == 1
        assert customer.email in mail.outbox[0].to


@pytest.mark.django_db
class TestAuthenticateCustomer(TestCase):
    """Tests for authentication."""

    def setUp(self):
        self.customer = Customer.objects.create_user(
            email='john@example.com',
            password='SecurePass123!'
        )

    def test_authenticate_success(self):
        """Authenticate with valid credentials."""
        customer = authenticate_customer('john@example.com', 'SecurePass123!')
        assert customer is not None
        assert customer.email == 'john@example.com'

    def test_authenticate_wrong_password(self):
        """Incorrect password."""
        customer = authenticate_customer('john@example.com', 'WrongPassword123!')
        assert customer is None

    def test_authenticate_nonexistent_email(self):
        """Email does not exist."""
        customer = authenticate_customer('nonexistent@example.com', 'SecurePass123!')
        assert customer is None