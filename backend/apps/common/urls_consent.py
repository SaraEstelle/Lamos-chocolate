from django.urls import path
from . import views
app_name = "consent"
urlpatterns = [path("set/", views.set_consent_view, name="set")]