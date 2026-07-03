"""
apps/b2b/tests/test_views.py
============================
L0 public funnel: pages, persistence, IP capture, emails, honeypot.
"""

import pytest
from django.urls import reverse

from apps.b2b.models import B2BRequest

VALID = {
    "company_name": "Hotel Beau-Rivage",
    "contact_name": "Jean Dupont",
    "contact_email": "jean@beaurivage.ch",
    "contact_phone": "+41 22 000 00 00",
    "sector": "Hospitality",
    "estimated_qty": 200,
    "occasion": "Christmas",
    "message": "We need branded chocolates.",
    "website": "",
}


@pytest.mark.django_db
class TestPublicFunnel:
    def test_presentation_ok(self, client):
        assert client.get(reverse("b2b:presentation")).status_code == 200

    def test_form_page_ok(self, client):
        assert client.get(reverse("b2b:request")).status_code == 200

    def test_valid_submission_creates_request_and_emails(self, client, mailoutbox):
        resp = client.post(reverse("b2b:request"), data=VALID)
        assert resp.status_code == 302
        req = B2BRequest.objects.get(company_name="Hotel Beau-Rivage")
        assert req.ip_address  # IP captured (anti-abuse)
        assert len(mailoutbox) == 2  # requester + internal

    def test_honeypot_blocks_persistence(self, client):
        client.post(reverse("b2b:request"), data={**VALID, "website": "http://bot"})
        assert not B2BRequest.objects.exists()

    def test_invalid_rerenders(self, client):
        resp = client.post(reverse("b2b:request"), data={**VALID, "contact_email": ""})
        assert resp.status_code == 200
        assert not B2BRequest.objects.exists()
