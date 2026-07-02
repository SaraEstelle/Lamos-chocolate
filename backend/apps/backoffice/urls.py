"""
apps/backoffice/urls.py
=======================
Staff-only backoffice routes.

Difference with /admin/:
- /admin/         → Django Admin (generic)
- /backoffice/    → Custom staff dashboard (KPIs, orders, stock, B2B)

Access is restricted to staff users (is_staff=True) at the view level.
"""

from django.urls import path

from . import views

app_name = "backoffice"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("orders/", views.orders_list_view, name="orders"),
    path("orders/<int:order_id>/status/", views.order_update_status_view, name="order_status"),
    path("stock/", views.stock_view, name="stock"),
    path("forecasting/", views.forecasting_view, name="forecasting"),
    path("b2b/", views.b2b_requests_view, name="b2b_requests"),
    path("b2b/<int:request_id>/status/", views.b2b_update_status_view, name="b2b_status"),
    # B2B pro-account validation (self-registered pending accounts).
    # B2BAccount.id is a UUID -> <uuid:...>.
    path("b2b-accounts/", views.b2b_accounts_view, name="b2b_accounts"),
    path("b2b-accounts/<uuid:account_id>/decision/",
         views.b2b_account_decision_view, name="b2b_account_decision"),
]
