"""
apps/common/consent.py
======================
Read / write the cookie-consent decision.

The decision is stored in a **first-party** cookie named `lamos_consent`, as a
small JSON payload. It is readable by the front-end JS (httponly=False) so the
page can decide whether to load analytics scripts *after* consent.
"""
import json
import secrets

from django.conf import settings

CONSENT_COOKIE = "lamos_consent"
CONSENT_MAX_AGE = 60 * 60 * 24 * 180          # 180 days, then we ask again
CONSENT_POLICY_VERSION = "1.0"   # bump this when the cookie/privacy policy changes

def read_consent(request) -> dict:
    """Return the visitor's consent as a dict, or safe defaults (nothing accepted)."""
    raw = request.COOKIES.get(CONSENT_COOKIE)
    if not raw:
        # No cookie yet -> the visitor has NOT decided. `set=False` = show the banner.
        return {"necessary": True, "analytics": False, "marketing": False, "set": False}
    try:
        data = json.loads(raw)
        data["set"] = True                    # a valid cookie means a decision was made
        return data
    except (ValueError, TypeError):
        # Corrupted cookie -> treat as "no decision".
        return {"necessary": True, "analytics": False, "marketing": False, "set": False}


def write_consent(response, *, analytics: bool, marketing: bool) -> str:
    """
    Persist the decision in the first-party cookie and return the consent_id.

    IMPORTANT: `secure` is True ONLY in production. In local dev we serve over
    plain HTTP (http://localhost:8000), and a `Secure` cookie would be silently
    dropped by the browser -> the banner would keep reappearing.
    """
    consent_id = secrets.token_urlsafe(16)
    payload = {
        "id": consent_id,
        "necessary": True,                    # strictly necessary is always on
        "analytics": bool(analytics),
        "marketing": bool(marketing),
        "policy_version": CONSENT_POLICY_VERSION,
    }
    response.set_cookie(
        CONSENT_COOKIE,
        json.dumps(payload),
        max_age=CONSENT_MAX_AGE,
        samesite="Lax",
        secure=not settings.DEBUG,            # 👈 THE FIX: no Secure flag in dev (HTTP)
        httponly=False,                       # readable by JS to gate analytics scripts
    )
    return consent_id


def analytics_allowed(request) -> bool:
    """True if the visitor accepted analytics (used to gate the Event tracking)."""
    return read_consent(request).get("analytics", False)


def marketing_allowed(request) -> bool:
    """True if the visitor accepted marketing cookies/scripts."""
    return read_consent(request).get("marketing", False)