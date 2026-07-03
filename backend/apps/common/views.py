import logging
import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.common.consent import write_consent, CONSENT_POLICY_VERSION
from apps.accounts.models import ConsentLog

logger = logging.getLogger(__name__)

@require_POST
def set_consent_view(request):
    """Record a consent decision (cookie + DB proof)."""
    try:
        body = json.loads(request.body or "{}")
    except ValueError:
        body = {}
    analytics = bool(body.get("analytics"))
    marketing = bool(body.get("marketing"))

    response = JsonResponse({"ok": True})
    consent_id = write_consent(response, analytics=analytics, marketing=marketing)

# 2) Store the immutable proof in DB (never breaks the response if it fails).
    try:
        ConsentLog.objects.create(
            customer=request.user if request.user.is_authenticated else None,
            consent_id=consent_id,
            necessary=True,
            analytics=analytics,
            marketing=marketing,
            policy_version=CONSENT_POLICY_VERSION,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        )
    except Exception:  # noqa: BLE001 - proof logging must not break the user flow
        # CORRECTION : on LOG l'échec au lieu de l'ignorer silencieusement.
        # Pour une preuve de conformité, un échec d'écriture doit être visible.
        logger.exception("Failed to write ConsentLog for consent_id=%s", consent_id)

    return response