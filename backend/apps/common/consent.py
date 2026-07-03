"""
apps/common/consent.py
======================
Helpers to read/write the cookie consent decision.
"""
import json
import secrets

CONSENT_COOKIE = "lamos_consent"
CONSENT_MAX_AGE = 60 * 60 * 24 * 180          # 180 days

def read_consent(request) -> dict:
    """Return the visitor's consent dict, or defaults (nothing accepted)."""
    raw = request.COOKIES.get(CONSENT_COOKIE)
    if not raw:
        return {"necessary": True, "analytics": False, "marketing": False, "set": False}
    try:
        data = json.loads(raw)
        data["set"] = True
        return data
    except (ValueError, TypeError):
        return {"necessary": True, "analytics": False, "marketing": False, "set": False}

def write_consent(response, *, analytics: bool, marketing: bool) -> str:
    """Persist the decision in a first-party cookie. Returns the consent_id."""
    consent_id = secrets.token_urlsafe(16)
    payload = {"id": consent_id, "necessary": True,
               "analytics": bool(analytics), "marketing": bool(marketing)}
    response.set_cookie(
        CONSENT_COOKIE, json.dumps(payload),
        max_age=CONSENT_MAX_AGE, samesite="Lax", secure=True, httponly=False,
        # httponly=False so the front JS can read it to gate client scripts.
    )
    return consent_id

def analytics_allowed(request) -> bool:
    return read_consent(request).get("analytics", False)