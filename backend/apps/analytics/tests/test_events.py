"""
apps/analytics/tests/test_events.py
===================================
Tests for event tracking and KPI selectors.
"""

import pytest

from apps.analytics.models import Event
from apps.analytics.selectors import channel_split, conversion_rate, revenue_by_canton
from apps.analytics.services import track_event


@pytest.mark.django_db
class TestTracking:
    def test_track_event_creates_row(self):
        track_event("product_view", channel="b2c", slug="kunafa")
        assert Event.objects.filter(event_type="product_view").count() == 1

    def test_tracking_never_raises_on_bad_input(self):
        result = track_event("purchase", value_chf="not-a-number")
        assert result is None or result.event_type == "purchase"


@pytest.mark.django_db
class TestKPISelectors:
    def test_revenue_by_canton(self):
        track_event("purchase", canton="VD", value_chf="50.00")
        track_event("purchase", canton="GE", value_chf="30.00")
        track_event("purchase", canton="VD", value_chf="20.00")
        result = {r["canton"]: r["total"] for r in revenue_by_canton()}
        assert result["VD"] == 70
        assert result["GE"] == 30

    def test_conversion_rate(self):
        for _ in range(10):
            track_event("product_view")
        track_event("purchase", value_chf="10.00")
        assert conversion_rate() == 0.1

    def test_channel_split(self):
        track_event("purchase", channel="b2c", value_chf="40.00")
        track_event("purchase", channel="b2b", value_chf="200.00")
        split = {r["channel"]: r["total"] for r in channel_split()}
        assert split["b2c"] == 40
        assert split["b2b"] == 200
