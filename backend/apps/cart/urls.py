from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_view, name="view"),
    path("add/", views.add_item_view, name="add"),
    path("update/", views.update_item_view, name="update"),
    path("remove/", views.remove_item_view, name="remove"),
]
