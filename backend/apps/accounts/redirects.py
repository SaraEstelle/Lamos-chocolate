"""
apps/accounts/redirects.py
==========================
Single source of truth for "where does a user land right after auth?".

Routing rules:
  - A user who owns a B2BAccount is a professional:
      * active account  -> the pro portal
      * any other status -> the pending/validation page
  - Everyone else (B2C) -> the customer area dashboard.
"""


def post_auth_redirect_target(user):
    """Return the URL *name* to redirect to after a successful login.

    Kept as a route name (not a resolved URL) so callers can pass it straight
    to django.shortcuts.redirect(), and allauth can reverse it too.
    """
    # getattr avoids a RelatedObjectDoesNotExist explosion when there is no
    # B2BAccount attached to this user.
    account = getattr(user, "b2b_account", None)
    if account is not None:
        return "b2b:portal" if account.status == "active" else "b2b:pending"
    return "customer_area:dashboard"
