from django.urls import path
from . import views

app_name = "checkout_webhook"

urlpatterns = [
    path("", views.stripe_webhook_view, name="stripe_webhook"),
]
