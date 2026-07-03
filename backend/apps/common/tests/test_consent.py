"""
apps/common/tests/test_consent.py
=================================
Tests for the cookie-consent endpoint and proof logging.
"""

import json

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import ConsentLog


@pytest.mark.integration
class TestConsent:
    def test_accept_sets_cookie_and_logs(self, client, db):
        url = reverse("consent:set")
        resp = client.post(
            url,
            data=json.dumps({"analytics": True, "marketing": False}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        # The cookie must be present on the response.
        assert "lamos_consent" in resp.cookies
        # A proof row must exist.
        log = ConsentLog.objects.latest("created_at")
        assert log.analytics is True
        assert log.marketing is False

    def test_reject_logs_all_false(self, client, db):
        url = reverse("consent:set")
        resp = client.post(
            url,
            data=json.dumps({"analytics": False, "marketing": False}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        log = ConsentLog.objects.latest("created_at")
        assert log.analytics is False and log.marketing is False


@pytest.mark.integration
class TestConsentExtra:
    def test_accept_records_policy_version(self, client, db):
        """La preuve doit porter la version de politique consentie (conformité)."""
        resp = client.post(
            reverse("consent:set"),
            data=json.dumps({"analytics": True, "marketing": False}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        log = ConsentLog.objects.latest("created_at")
        assert log.policy_version  # non vide (ex. "1.0")
        assert log.necessary is True  # strictement nécessaire toujours vrai

    def test_endpoint_rejects_post_without_csrf(self, db):
        """
        Avec CSRF ACTIVÉ (comme un vrai navigateur SANS token), l'endpoint doit
        renvoyer 403. Cela documente le fait que l'endpoint est bien protégé.
        """
        csrf_client = Client(enforce_csrf_checks=True)  # 👈 CSRF réellement vérifié
        resp = csrf_client.post(
            reverse("consent:set"),
            data=json.dumps({"analytics": True, "marketing": False}),
            content_type="application/json",
        )
        assert resp.status_code == 403  # protégé : bon signe de sécurité
