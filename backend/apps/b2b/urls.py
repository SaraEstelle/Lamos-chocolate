"""
apps/b2b/urls.py
================
B2B routes.NOTE: B2BRequest and Order use INTEGER primary keys → <int:...>.
"""

from django.urls import path

from . import views

app_name = "b2b"

urlpatterns = [
    # L0 — public funnel
    path("", views.presentation_view, name="presentation"),
    path("access/", views.access_view, name="access"),
    path("request/", views.request_form_view, name="request"),
    path("request/success/", views.success_view, name="success"),

    # L1 — pro space (login + B2BAccount)
    path("portal/", views.portal_home_view, name="portal"),
    path("portal/in-progress/", views.in_progress_view, name="in_progress"),
    path("portal/catalogue/", views.portal_catalogue_view, name="catalogue"),
    path("portal/history/", views.portal_history_view, name="history"),
    path("portal/history/export/", views.history_export_view, name="history_export"),
    path("portal/exclusive/", views.exclusive_view, name="exclusive"),
    path("portal/reorder/<int:order_id>/", views.reorder_view, name="reorder"),

    # L2 — configurator
    path("configurator/", views.configurator_view, name="configurator"),

    path("register/account/", views.register_view, name="register"),
    path("pending/", views.pending_view, name="pending"),

    path("portal/documents/", views.documents_view, name="documents"),
    path("portal/notifications/", views.notifications_view, name="notifications"),
    path("portal/profile/", views.company_profile_view, name="profile"),
]