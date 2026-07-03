"""
apps/common/urls_consent.py
===========================
Consent endpoint. Mounted OUTSIDE i18n_patterns so it is reachable at a stable
URL (/consent/set/) regardless of the active language.
"""
from django.urls import path

from . import views

app_name = "consent"

urlpatterns = [
    path("set/", views.set_consent_view, name="set"),
]