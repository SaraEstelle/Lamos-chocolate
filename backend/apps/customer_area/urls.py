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
    path("password/", views.password_change_view, name="password_change"),
    path("invoices/", views.invoices_view, name="invoices"),
    path("invoices/<int:order_id>/", views.invoice_detail_view, name="invoice_detail"),
    path("data-export/", views.data_export_view, name="data_export"),
    # Addresses
    path("addresses/", views.addresses_view, name="addresses"),
    path("addresses/new/", views.address_create_view, name="address_create"),
    path(
        "addresses/<uuid:address_id>/edit/",
        views.address_edit_view,
        name="address_edit",
    ),
    path(
        "addresses/<uuid:address_id>/delete/",
        views.address_delete_view,
        name="address_delete",
    ),
]
