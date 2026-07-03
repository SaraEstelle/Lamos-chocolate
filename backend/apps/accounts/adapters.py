"""
apps/accounts/adapters.py
=========================
Custom allauth adapter: ensures social sign-ups create well-formed B2C
Customers (first/last name filled, B2C type) and never escalate privileges.
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse

from apps.accounts.redirects import post_auth_redirect_target
from apps.common.constants import CustomerTypeChoices


class LamosSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        # Let allauth map email/first/last name, then enforce our defaults.
        user = super().populate_user(request, sociallogin, data)
        user.first_name = (data.get("first_name") or user.first_name or "").strip()
        user.last_name = (data.get("last_name") or user.last_name or "").strip()
        user.is_b2b = False
        user.customer_type = CustomerTypeChoices.B2C
        return user

    def is_open_for_signup(self, request, sociallogin):
        # B2C social sign-up is allowed. (B2B never self-creates via social.)
        return True


class LamosAccountAdapter(DefaultAccountAdapter):
    """Route users to the right area after an allauth (e.g. Google) login."""

    def get_login_redirect_url(self, request):
        target = post_auth_redirect_target(request.user)
        return reverse(target)
