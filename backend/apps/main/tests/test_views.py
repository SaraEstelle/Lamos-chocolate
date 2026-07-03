"""
apps/main/tests/test_views.py
=============================
Tests for the public main pages.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestPublicPages:
    def test_home_returns_200(self, client):
        assert client.get(reverse("main:home")).status_code == 200

    def test_about_returns_200(self, client):
        assert client.get(reverse("main:about")).status_code == 200

    def test_privacy_returns_200(self, client):
        assert client.get(reverse("main:privacy")).status_code == 200

    def test_terms_returns_200(self, client):
        assert client.get(reverse("main:terms")).status_code == 200

    def test_contact_get_returns_200(self, client):
        assert client.get(reverse("main:contact")).status_code == 200

    def test_contact_post_valid_redirects(self, client):
        resp = client.post(
            reverse("main:contact"),
            data={
                "name": "Test",
                "email": "test@example.com",
                "message": "Hello",
            },
        )
        assert resp.status_code == 302
