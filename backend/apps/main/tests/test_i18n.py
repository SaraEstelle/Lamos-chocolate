"""Smoke tests for internationalization (i18n) routing and language switching."""

import pytest
from django.urls import reverse


@pytest.mark.integration
class TestI18n:
    def test_set_language_to_de_ch(self, client, db):
        """Switching to Swiss German should redirect (302) or render (200)."""
        response = client.post(
            reverse("set_language"),
            data={"language": "de-ch", "next": "/"},
        )
        assert response.status_code in (302, 200)

    def test_set_language_to_it_ch(self, client, db):
        """Switching to Swiss Italian should redirect (302) or render (200)."""
        response = client.post(
            reverse("set_language"),
            data={"language": "it-ch", "next": "/"},
        )
        assert response.status_code in (302, 200)

    def test_de_ch_prefixed_home_is_reachable(self, client, db):
        """The /de-ch/ language-prefixed homepage should not 404."""
        response = client.get("/de-ch/")
        assert response.status_code in (200, 301, 302)
