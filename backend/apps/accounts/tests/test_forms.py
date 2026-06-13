"""
apps/accounts/tests/test_forms.py
==================================
Tests for authentication forms.

Tests:
- RegisterForm: email unique, password complexity
- LoginForm: valid credentials
- PasswordResetForm: email exists
- PasswordResetConfirmForm: password match

Coverage: ~100% of form validation
"""

import pytest
from django.test import TestCase
from apps.accounts.models import Customer
from apps.accounts.forms import (
    RegisterForm, LoginForm, PasswordResetForm, PasswordResetConfirmForm
)


@pytest.mark.django_db
class TestRegisterForm(TestCase):
    """Tests for registration form."""

    def test_register_form_valid(self):
        """Registration with valid data."""
        form_data = {
            'email': 'john@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+41791234567',
            'preferred_language': 'en'
        }
        form = RegisterForm(data=form_data)
        assert form.is_valid(), f"Form errors:{form.errors}"

    def test_register_form_password_weak(self):
        """Password too weak (< 12 chars)."""
        form_data = {
            'email': 'john@example.com',
            'password': 'weak123',
            'password_confirm': 'weak123',
            'first_name': 'John',
            'last_name': 'Doe',
        }
        form = RegisterForm(data=form_data)
        assert not form.is_valid()
        assert 'password' in form.errors

    def test_register_form_password_no_special_char(self):
        """Password without special character."""
        form_data = {
            'email': 'john@example.com',
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123',
            'first_name': 'John',
            'last_name': 'Doe',
        }
        form = RegisterForm(data=form_data)
        assert not form.is_valid()
        assert 'password' in form.errors

    def test_register_form_password_mismatch(self):
        """Passwords do not match."""
        form_data = {
            'email': 'john@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!',
            'first_name': 'John',
            'last_name': 'Doe',
        }
        form = RegisterForm(data=form_data)
        assert not form.is_valid()

    def test_register_form_email_duplicate(self):
        """Email already in use."""
        Customer.objects.create_user(
            email='john@example.com',
            password='SecurePass123!'
        )

        form_data = {
            'email': 'john@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe',
        }
        form = RegisterForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_register_form_invalid_email(self):
        """Invalid email format."""
        form_data = {
            'email': 'not-an-email',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe',
        }
        form = RegisterForm(data=form_data)
        assert not form.is_valid()
        assert 'email' in form.errors


@pytest.mark.django_db
class TestLoginForm(TestCase):
    """Tests for login form."""

    def setUp(self):
        self.customer = Customer.objects.create_user(
            email='john@example.com',
            password='SecurePass123!'
        )

    def test_login_form_valid(self):
        """Login with valid credentials."""
        form_data = {
            'email': 'john@example.com',
            'password': 'SecurePass123!',
        }
        form = LoginForm(data=form_data)
        assert form.is_valid(), f"Form errors:{form.errors}"
        assert form.customer == self.customer

    def test_login_form_invalid_password(self):
        """Incorrect password."""
        form_data = {
            'email': 'john@example.com',
            'password': 'WrongPassword123!',
        }
        form = LoginForm(data=form_data)
        assert not form.is_valid()

    def test_login_form_nonexistent_email(self):
        """Email does not exist."""
        form_data = {
            'email': 'nonexistent@example.com',
            'password': 'SecurePass123!',
        }
        form = LoginForm(data=form_data)
        assert not form.is_valid()


@pytest.mark.django_db
class TestPasswordResetForm(TestCase):
    """Tests for password reset form."""

    def setUp(self):
        Customer.objects.create_user(
            email='john@example.com',
            password='SecurePass123!'
        )

    def test_password_reset_form_valid(self):
        """Valid email."""
        form_data = {'email': 'john@example.com'}
        form = PasswordResetForm(data=form_data)
        assert form.is_valid()

    def test_password_reset_form_invalid_email(self):
        """Invalid email format."""
        form_data = {'email': 'not-an-email'}
        form = PasswordResetForm(data=form_data)
        assert not form.is_valid()


@pytest.mark.django_db
class TestPasswordResetConfirmForm(TestCase):
    """Tests for new password form."""

    def test_password_reset_confirm_form_valid(self):
        """Valid new password."""
        form_data = {
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!',
        }
        form = PasswordResetConfirmForm(data=form_data)
        assert form.is_valid()

    def test_password_reset_confirm_form_mismatch(self):
        """Passwords do not match."""
        form_data = {
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'DifferentPass123!',
        }
        form = PasswordResetConfirmForm(data=form_data)
        assert not form.is_valid()

    def test_password_reset_confirm_form_weak(self):
        """Password too weak."""
        form_data = {
            'new_password': 'weak123',
            'new_password_confirm': 'weak123',
        }
        form = PasswordResetConfirmForm(data=form_data)
        assert not form.is_valid()