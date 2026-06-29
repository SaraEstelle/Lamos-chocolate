from django.urls import path

from . import webhooks

app_name = "checkout_webhook"

urlpatterns = [
    path("", webhooks.stripe_webhook_view, name="stripe_webhook"),
]
