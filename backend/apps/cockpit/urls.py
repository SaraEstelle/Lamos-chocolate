"""
apps/cockpit/urls.py
====================
Executive cockpit routes (staff-only, standalone executive layer).
"""

from django.urls import path

from . import views

app_name = "cockpit"

urlpatterns = [
    path("", views.cockpit_view, name="dashboard"),
    path("heatmap/", views.heatmap_view, name="heatmap"),
    path("products/", views.products_view, name="products"),
    path("products/<int:product_id>/", views.product_detail_view, name="product_detail"),
    path("inventory/", views.inventory_view, name="inventory"),
    path("pilotage/", views.pilotage_view, name="pilotage"),
    path("etude/", views.etude_view, name="etude"),
]
