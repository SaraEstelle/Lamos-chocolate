import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.common.consent import write_consent
from apps.accounts.models import ConsentLog

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

    ConsentLog.objects.create(
        customer=request.user if request.user.is_authenticated else None,
        consent_id=consent_id, analytics=analytics, marketing=marketing,
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
    )
    return response