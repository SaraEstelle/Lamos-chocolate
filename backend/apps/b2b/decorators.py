"""
apps/b2b/decorators.py
======================
Access control for the authenticated B2B pro space.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def b2b_account_required(view_func):
    """
    Allow only authenticated users that own a B2BAccount.

    Non-pro users are silently redirected to the public B2B page (no information
    leak about protected resources). The account is attached to request for
    convenience as request.b2b_account.
    """
    @wraps(view_func)
    @login_required(login_url="accounts:login")
    def _wrapped(request, *args, **kwargs):
        account = getattr(request.user, "b2b_account", None)
        if account is None:
            return redirect("b2b:presentation")
        if account.status != "active":
            return redirect("b2b:pending")
        request.b2b_account = account
        return view_func(request, *args, **kwargs)

    return _wrapped

def b2b_login_required(view_func):
    """
    Lighter gate than b2b_account_required: the user must be authenticated and
    own a B2BAccount, but ANY status is accepted (prospect/pending/active).

    Used for read-only resources a not-yet-validated partner may already see,
    e.g. the downloadable B2B catalogue. Ordering/quoting stays behind
    b2b_account_required (active only).
    """
    @wraps(view_func)
    @login_required(login_url="accounts:login")
    def _wrapped(request, *args, **kwargs):
        account = getattr(request.user, "b2b_account", None)
        if account is None:
            return redirect("b2b:presentation")   # not a pro → public page
        request.b2b_account = account
        return view_func(request, *args, **kwargs)

    return _wrapped