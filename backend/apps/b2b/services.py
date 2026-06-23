"""
apps/b2b/services.py
====================
Business logic for the public B2B funnel: IP extraction, rate limiting,
persistence side-effects, email notifications and event tracking.
"""

import logging

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from decimal import Decimal
from apps.b2b.models import DEFAULT_B2B_MOQ, QuoteSimulation

from apps.analytics.services import track_event

logger = logging.getLogger(__name__)

B2B_THROTTLE_MAX = 5
B2B_THROTTLE_WINDOW = 60 * 60  # 1 hour


def get_client_ip(request):
    """Best-effort extraction of the client IP from the request."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def is_rate_limited(ip_address):
    """Return True if this IP exceeded B2B_THROTTLE_MAX submissions in the window."""
    if not ip_address:
        return False
    key = f"b2b_throttle:{ip_address}"
    cache.add(key, 0, timeout=B2B_THROTTLE_WINDOW)
    try:
        current = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=B2B_THROTTLE_WINDOW)
        current = 1
    return current > B2B_THROTTLE_MAX


def notify_b2b_request(b2b_request, *, wants_marketing=False):
    """Email the requester (confirmation) and the team (notification). Never raises."""
    try:
        send_mail(
            subject="Lamos Chocolate — Request received",
            message=render_to_string("emails/b2b_request_confirmation.txt", {"req": b2b_request}),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[b2b_request.contact_email],
            fail_silently=True,
        )
        send_mail(
            subject=f"New B2B request from{b2b_request.company_name}",
            message=render_to_string(
                "emails/b2b_request_internal.txt",
                {"req": b2b_request, "wants_marketing": wants_marketing},
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
            fail_silently=True,
        )
        return True
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send B2B notification emails")
        return False


def create_b2b_request(form, *, request):
    """Persist a validated B2BRequest, store consent, notify, and track the event."""
    b2b_request = form.save(commit=False)
    b2b_request.ip_address = get_client_ip(request)
    b2b_request.language = getattr(request, "LANGUAGE_CODE", "fr")[:2]

    # Store marketing consent WITH a timestamp (nLPD proof of consent).
    wants_marketing = form.cleaned_data.get("wants_marketing", False)
    b2b_request.wants_marketing = wants_marketing
    if wants_marketing:
        b2b_request.marketing_consent_at = timezone.now()
    b2b_request.save()

    notify_b2b_request(b2b_request, wants_marketing=wants_marketing)
    track_event("b2b_request_submitted", channel="b2b",
                company=b2b_request.company_name)
    return b2b_request

def simulate_quote(account, *, sku, quantity):
    """
    Compute the estimated value + MOQ status for one configured SKU and persist
    a QuoteSimulation (this is what the "% simulations >= MOQ" KPI counts).

    Returns a dict with the numbers the template needs.
    """
    info = getattr(sku, "b2b_info", None)
    moq = info.moq if info else DEFAULT_B2B_MOQ
    unit_price = info.effective_price if info else sku.price
    estimated = Decimal(unit_price) * quantity
    moq_reached = quantity >= moq
    lines = [{"sku": sku.sku_code, "qty": quantity, "price": str(unit_price)}]

    sim = QuoteSimulation.objects.create(
        account=account, cart_json=lines,
        estimated_value=estimated, moq_reached=moq_reached,
    )
    return {
        "sim": sim, "moq": moq, "moq_reached": moq_reached,
        "unit_price": unit_price, "estimated": estimated,
    }


def notify_quote_request(account, customization, estimated):
    """Email the sales team that a pro requested a formal quote. Never raises."""
    try:
        send_mail(
            subject=f"B2B quote requested —{account.company_name}",
            message=(
                f"Account:{account.company_name}\n"
                f"SKU:{customization.sku.sku_code}\n"
                f"Quantity:{customization.quantity}\n"
                f"Logo engraved:{customization.logo_engraved}\n"
                f"Inner packaging:{customization.inner_packaging}\n"
                f"Outer packaging:{customization.outer_packaging}\n"
                f"Grammage:{customization.grammage}\n"
                f"Estimated value:{estimated} CHF\n"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
            fail_silently=True,
        )
        return True
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send B2B quote-request email")
        return False

