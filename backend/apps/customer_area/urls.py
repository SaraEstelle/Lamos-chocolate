"""
apps/customer_area/urls.py
==========================
Routes for the authenticated customer area (my-account).

Note: Order.id is a BigAutoField (int), so order_id uses <int:...>,
NOT <uuid:...>.

Authentication: REQUIRED (enforced in the views via @login_required).
"""

from django.urls import path

from . import views

app_name = "customer_area"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("orders/", views.orders_view, name="orders"),
    path("orders/<int:order_id>/", views.order_detail_view, name="order_detail"),
    path("profile/", views.profile_view, name="profile"),
]