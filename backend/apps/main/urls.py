"""
apps/main/urls.py
=================
Routes for the public main app (homepage + static pages).
No authentication required.
"""

from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("about/", views.about_view, name="about"),
    path("privacy/", views.privacy_view, name="privacy"),
    path("terms/", views.terms_view, name="terms"),
    path("contact/", views.contact_view, name="contact"),
]