"""
apps/accounts/urls.py
=====================
Routing for authentication.

Routes:
- /register/
- /login/
- /logout/
- /password-reset/
- /password-reset-confirm/<token>/
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path("connect/", views.connect_view, name="connect"),

    # Registration
    path('register/', views.register_view, name='register'),

    # Login
    path('login/', views.login_view, name='login'),

    # Logout
    path('logout/', views.logout_view, name='logout'),

    # Password reset (step 1)
    path('password-reset/', views.password_reset_view, name='password_reset'),

    # Password reset (step 2 - via email link)
    path('password-reset-confirm/<str:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
]