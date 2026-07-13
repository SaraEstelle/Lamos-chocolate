"""
apps/accounts/views.py
======================
Views for authentication (HTTP views).

5 main views:
1. register_view() — User registration
2. login_view() — User login
3. logout_view() — User logout
4. password_reset_view() — Password reset request
5. password_reset_confirm_view() — New password

Security:
- CSRF tokens (Django provides automatically)
- Rate limiting (optional: django-ratelimit)
- Logging of all sensitive actions
- Secure redirects
"""

import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from apps.accounts.forms import (
    LoginForm,
    PasswordResetConfirmForm,
    PasswordResetForm,
    RegisterForm,
)
from apps.accounts.models import Customer
from apps.accounts.redirects import post_auth_redirect_target
from apps.accounts.services import create_customer, send_password_reset_email
from apps.accounts.tokens import (
    create_reset_token,
    mark_token_as_used,
    verify_reset_token,
)

logger = logging.getLogger("apps.accounts")


@require_http_methods(["GET"])
def connect_view(request):
    """Profile chooser (B2C / B2B) + quick login entry point."""
    if request.user.is_authenticated:
        return redirect(post_auth_redirect_target(request.user))
    return render(request, "accounts/connect.html")


@require_http_methods(["GET", "POST"])
@csrf_protect
def register_view(request):
    """
    User registration view.

    GET  : Display registration form
    POST : Process registration

    Process POST:
    1. Validate the form
    2. Create the customer
    3. Send welcome email
    4. Redirect to login

    Template: accounts/register.html
    """

    if request.method == "GET":
        # Display the form
        form = RegisterForm()
        return render(request, "accounts/register.html", {"form": form})

    elif request.method == "POST":
        # Process registration
        form = RegisterForm(request.POST)

        if form.is_valid():
            try:
                # Create the customer
                customer = create_customer(
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    preferred_language=form.cleaned_data.get(
                        "preferred_language", "fr"
                    ),
                )

                logger.info(f"New customer registered:{customer.email}")

                # Success message
                messages.success(
                    request,
                    "Registration successful! Check your email. " "You can now log in.",
                )

                # Redirect to login
                return redirect("accounts:login")

            except ValueError as e:
                # Email already exists
                logger.warning(f"Registration failed:{str(e)}")
                messages.error(request, str(e))
                return render(request, "accounts/register.html", {"form": form})

            except Exception as e:
                # Server error
                logger.error(f"Registration error:{str(e)}")
                messages.error(request, "An error occurred. Please try again later.")
                return render(request, "accounts/register.html", {"form": form})

        else:
            # Form is invalid
            logger.warning(f"Invalid registration form:{form.errors}")
            return render(request, "accounts/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
@csrf_protect
def login_view(request):
    """
    User login view.

    GET  : Display login form
    POST : Process login

    Process POST:
    1. Validate the form
    2. Authenticate the customer
    3. Create the session
    4. Redirect to account or requested page

    Template: accounts/login.html
    """

    if request.method == "GET":
        form = LoginForm()
        return render(request, "accounts/login.html", {"form": form})

    elif request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            # form.clean() already verified credentials
            customer = form.customer

            # Create the session
            login(request, customer)

            # Handle "stay logged in"
            if form.cleaned_data.get("remember_me"):
                # Session valid for 2 weeks
                request.session.set_expiry(1209600)  # 14 days in seconds

            logger.info(f"Customer logged in:{customer.email}")

            # Success message
            messages.success(request, f"Welcome{customer.first_name}! 👋")

            # Redirect to "next" only if it is a safe internal URL.
            # Prevents Open Redirect attacks (e.g. ?next=https://evil.com).
            next_url = request.GET.get("next")
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect(post_auth_redirect_target(customer))

        else:
            # Form is invalid (incorrect email/password)
            logger.warning(
                f"Failed login attempt from{request.META.get('REMOTE_ADDR')}"
            )
            messages.error(request, "Incorrect email or password.")
            return render(request, "accounts/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
@csrf_protect
def access_view(request):
    """
    Combined B2C access page: sign-in AND sign-up on one sliding card.

    - GET ?mode=register  -> opens on the sign-up side.
    - POST form_type=login    -> authenticate + redirect (open-redirect safe).
    - POST form_type=register -> create customer, store nLPD consent, then
      send the user to the sign-in side to log in.

    We keep the legacy login_view / register_view untouched (tests rely on them).
    Template: accounts/access.html
    """
    # Already logged in? Skip the page entirely.
    if request.user.is_authenticated:
        return redirect(post_auth_redirect_target(request.user))

    login_form = LoginForm()
    register_form = RegisterForm()
    # Which side is open when we render (default = sign-in).
    active_panel = "register" if request.GET.get("mode") == "register" else "signin"

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        # ---------- SIGN UP (B2C) ----------
        if form_type == "register":
            active_panel = "register"  # stay on this side if anything fails
            register_form = RegisterForm(request.POST)

            # nLPD / GDPR consent is a hard requirement for account creation.
            if not request.POST.get("gdpr"):
                register_form.add_error(None, "You must accept the privacy policy.")

            if register_form.is_valid():
                try:
                    customer = create_customer(
                        email=register_form.cleaned_data["email"],
                        password=register_form.cleaned_data["password"],
                        first_name=register_form.cleaned_data["first_name"],
                        last_name=register_form.cleaned_data["last_name"],
                        preferred_language=register_form.cleaned_data.get("preferred_language")
                        or "fr",
                        )
                    # Store consent WITH a timestamp (Swiss nLPD proof of consent).
                    customer.consent_nlpd = True
                    customer.consent_nlpd_at = timezone.now()
                    customer.save(update_fields=["consent_nlpd", "consent_nlpd_at"])

                    logger.info(f"New B2C customer via access page:{customer.email}")
                    messages.success(request, "Account created! You can now sign in.")
                    # Bounce to the sign-in side of the same page.
                    return redirect(reverse("accounts:access"))
                except ValueError as e:
                    register_form.add_error("email", str(e))

        # ---------- SIGN IN ----------
        else:
            active_panel = "signin"
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                customer = login_form.customer  # set in LoginForm.clean()
                login(request, customer)
                if login_form.cleaned_data.get("remember_me"):
                    request.session.set_expiry(1209600)  # 14 days
                logger.info(f"Customer logged in via access page:{customer.email}")

                # Honour a safe internal ?next=, else the role-based landing page.
                next_url = request.GET.get("next")
                if next_url and url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)
                return redirect(post_auth_redirect_target(customer))

    return render(
        request,
        "accounts/access.html",
        {
            "login_form": login_form,
            "register_form": register_form,
            "active_panel": active_panel,
        },
    )


@require_http_methods(["GET"])
@login_required(login_url="accounts:login")
def logout_view(request):
    """
    User logout view.

    GET : Logout and redirect to home

    Security: @login_required to prevent non-authenticated users calling it
    """

    # Logout
    logout(request)

    logger.info("Customer logged out")

    # Success message
    messages.success(request, "You have been logged out. See you! 👋")

    # Redirect to home
    return redirect("main:home")


@require_http_methods(["GET", "POST"])
@csrf_protect
def password_reset_view(request):
    """
    Password reset request view.

    GET  : Display "forgot password" form
    POST : Send reset link

    Process POST:
    1. Validate the email
    2. Find the customer
    3. Create a PasswordResetToken
    4. Send the email
    5. Display "email sent" message

    Security: Don't reveal if email exists or not

    Template: accounts/password_reset.html
    """

    if request.method == "GET":
        form = PasswordResetForm()
        return render(request, "accounts/password_reset.html", {"form": form})

    elif request.method == "POST":
        form = PasswordResetForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]

            try:
                # Find the customer
                customer = Customer.objects.get(email=email)

                # Create a token
                token = create_reset_token(customer)

                # Send the email
                send_password_reset_email(customer, token)

                logger.info(f"Password reset email sent to{email}")

            except Customer.DoesNotExist:
                # Email does not exist, but show same message
                # (security: don't reveal if email exists)
                logger.warning(f"Password reset for non-existent email:{email}")
                pass

            except Exception as e:
                # Server error
                logger.error(f"Password reset error for{email}:{str(e)}")

            # Always show same message (security)
            messages.success(
                request,
                "If this email is registered, you will receive a password reset link.",
            )

            # Redirect to login
            return redirect("accounts:login")

        else:
            return render(request, "accounts/password_reset.html", {"form": form})


@require_http_methods(["GET", "POST"])
@csrf_protect
def password_reset_confirm_view(request, token):
    """
    Password reset confirmation view (via email link).

    GET  : Display new password form
    POST : Save new password

    Args:
        token (str): The token from the email link

    Process:
    1. Verify that token is valid
    2. If expired: show error
    3. If used: show error
    4. Display the form
    5. User enters new password
    6. Save the new password
    7. Mark token as used
    8. Redirect to login

    Template: accounts/password_reset_confirm.html
    """

    # Verify the token
    token_obj = verify_reset_token(token)

    if not token_obj:
        # Token is invalid, expired, or already used
        logger.warning(f"Invalid password reset token:{token}")
        messages.error(
            request, "This link is invalid or expired. " "Please request a new link."
        )
        return redirect("accounts:password_reset")

    if request.method == "GET":
        # Display the form
        form = PasswordResetConfirmForm()
        return render(request, "accounts/password_reset_confirm.html", {"form": form})

    elif request.method == "POST":
        form = PasswordResetConfirmForm(request.POST)

        if form.is_valid():
            try:
                # Get the customer
                customer = token_obj.customer

                # Save the new password
                customer.set_password(form.cleaned_data["new_password"])
                customer.save()

                # Mark the token as used
                mark_token_as_used(token_obj)

                logger.info(f"Password reset successful for{customer.email}")

                messages.success(
                    request, "Your password has been reset. " "You can now log in."
                )

                # Redirect to login
                return redirect("accounts:login")

            except Exception as e:
                logger.error(f"Password reset confirm error:{str(e)}")
                messages.error(request, "An error occurred. Please try again.")
                return render(
                    request, "accounts/password_reset_confirm.html", {"form": form}
                )

        else:
            return render(
                request, "accounts/password_reset_confirm.html", {"form": form}
            )
