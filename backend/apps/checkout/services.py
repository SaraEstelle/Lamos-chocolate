"""
apps/checkout/emails.py
=======================
Transactional emails for the checkout flow.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _send_html_email(subject, to_email, template, context):
    """Render an HTML template and send it (with a plain-text fallback)."""
    try:
        html_body = render_to_string(template, context)
        msg = EmailMultiAlternatives(
            subject=subject,
            body="Please view this email in an HTML-capable client.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        return True
    except Exception:  # noqa: BLE001 - never break the flow on email error
        logger.exception("Failed to send email:%s", template)
        return False


def send_order_confirmation(order):
    """Send the order confirmation email to the customer."""
    return _send_html_email(
        subject="Order confirmation — Lamos Chocolate",
        to_email=order.customer.email,
        template="emails/order_confirmation.html",
        context={"order": order},
    )


def send_order_shipped(order):
    """Send the shipping notification email to the customer."""
    return _send_html_email(
        subject="Your order has shipped — Lamos Chocolate",
        to_email=order.customer.email,
        template="emails/order_shipped.html",
        context={"order": order},
    )