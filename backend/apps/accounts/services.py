"""
apps/accounts/services.py
=========================
Business logic for authentication.

Responsibilities:
1. create_customer() — Create a new customer
2. send_welcome_email() — Send onboarding email
3. send_password_reset_email() — Send password reset link
4. authenticate_customer() — Verify email + password

Security:
- Logging of all failed attempts
- No information revelation
- Emails sent asynchronously (optional: with Celery)
"""

import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from apps.accounts.models import Customer, PasswordResetToken
from apps.accounts.tokens import create_reset_token


# Logger for failed attempts
logger = logging.getLogger('apps.accounts')


def create_customer(email: str, password: str, first_name: str, last_name: str,
                    phone: str = "", preferred_language: str = "fr", **kwargs) -> Customer:
    """
    Create a new customer with validation.

    Process:
    1. Check that email is unique
    2. Create the customer
    3. Hash and save the password
    4. Send welcome email

    Args:
        email (str): Unique customer email
        password (str): Password (will be hashed)
        first_name (str): First name
        last_name (str): Last name
        phone (str, optional): Phone number
        preferred_language (str, optional): Preferred language (fr, en, de-ch, it-ch)

    Return:
        Customer: The created customer

    Raises:
        ValueError: If email already exists

    Example:
        customer = create_customer(
            email="john@example.com",
            password="SecurePass123!",
            first_name="John",
            last_name="Doe"
        )
    """
    # 1. Check email is unique
    if Customer.objects.filter(email=email).exists():
        logger.warning(f"Registration attempt with existing email:{email}")
        raise ValueError(f"Email{email} is already in use.")

    # 2. Create the customer
    customer = Customer.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        preferred_language=preferred_language,
        is_active=True  # Customer is active immediately
    )

    logger.info(f"New customer created:{email}")

    # 3. Send welcome email
    try:
        send_welcome_email(customer)
    except Exception as e:
        # Log the error but don't block customer creation
        logger.error(f"Failed to send welcome email to{email}:{str(e)}")

    return customer


def send_welcome_email(customer: Customer) -> bool:
    """
    Send welcome email to customer.

    Template: templates/emails/welcome.html

    Content:
    - Welcome {first_name}
    - Link to /en/accounts/login/
    - Privacy policy

    Args:
        customer (Customer): The customer to send email to

    Return:
        bool: True if success, False otherwise

    Example:
        sent = send_welcome_email(customer)
        if sent:
            print("Email sent successfully")
    """
    try:
        # Email content
        subject = f"Welcome{customer.first_name}! 🍫"

        # Render HTML template
        html_message = render_to_string(
            'emails/welcome.html',
            {
                'customer': customer,
                'login_url': f"{settings.SITE_URL}/en/accounts/login/",
                'company_name': 'Lamos Chocolate'
            }
        )

        # Send the email
        send_mail(
            subject=subject,
            message="",  # Text message (we use HTML)
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[customer.email],
            html_message=html_message,
            fail_silently=False
        )

        logger.info(f"Welcome email sent to{customer.email}")
        return True

    except Exception as e:
        logger.error(f"Error sending welcome email to{customer.email}:{str(e)}")
        return False


def send_password_reset_email(customer: Customer, token: PasswordResetToken) -> bool:
    """
    Send password reset link via email.

    Template: templates/emails/reset_password.html

    Content:
    - Reset link: /en/accounts/password-reset-confirm/{token}/
    - "Expires in 24h"
    - "If you didn't request this, ignore this email"

    Args:
        customer (Customer): The customer
        token (PasswordResetToken): The created token

    Return:
        bool: True if success, False otherwise

    Example:
        token = create_reset_token(customer)
        sent = send_password_reset_email(customer, token)
    """
    try:
        # Build reset link
        reset_url = f"{settings.SITE_URL}/en/accounts/password-reset-confirm/{token.token}/"

        # Render template
        html_message = render_to_string(
            'emails/reset_password.html',
            {
                'customer': customer,
                'reset_url': reset_url,
                'expires_in_hours': 24,
                'company_name': 'Lamos Chocolate'
            }
        )

        # Send the email
        send_mail(
            subject="Reset your Lamos Chocolate password",
            message="",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[customer.email],
            html_message=html_message,
            fail_silently=False
        )

        logger.info(f"Password reset email sent to{customer.email}")
        return True

    except Exception as e:
        logger.error(f"Error sending password reset email to{customer.email}:{str(e)}")
        return False


def authenticate_customer(email: str, password: str) -> Customer | None:
    """
    Authenticate a customer (verify email + password).

    Process:
    1. Find the customer by email
    2. Verify the password (hashed)
    3. Log failed attempts

    Args:
        email (str): Customer email
        password (str): Password in plaintext

    Return:
        Customer if valid, None otherwise

    Example:
        customer = authenticate_customer("john@example.com", "MySecurePass123!")
        if customer:
            # Login successful
            login(request, customer)
        else:
            # Login failed
            print("Incorrect email or password")
    """
    try:
        # Find the customer
        customer = Customer.objects.get(email=email)

        # Verify the password
        if customer.check_password(password):
            # ✅ Password is correct
            logger.info(f"Successful login:{email}")
            return customer
        else:
            # ❌ Password is incorrect
            logger.warning(f"Failed login (wrong password):{email}")
            return None

    except Customer.DoesNotExist:
        # ❌ Email does not exist
        logger.warning(f"Failed login (email not found):{email}")
        return None

    except Exception as e:
        # ❌ Server error
        logger.error(f"Error during authentication:{str(e)}")
        return None
