"""
apps/accounts/urls.py
=====================
Routes d'authentification et gestion de compte.

Contenu :
- Inscription (register)
- Connexion (login)
- Déconnexion (logout)
- Réinitialisation de mot de passe (password_reset)
- Confirmation d'email (email_verify)

Règulation Suisse (RGPD) :
- Vérification d'email obligatoire
- Mot de passe sécurisé (12+ caractères, complexe)
- Droit d'accès et suppression des données
"""

from django.urls import path

# Nom de cette app
app_name = 'accounts'

# Routes d'authentification
urlpatterns = [
    # path('register/', views.register_view, name='register'),                    # Inscription
    # path('login/', views.login_view, name='login'),                            # Connexion
    # path('logout/', views.logout_view, name='logout'),                         # Déconnexion
    # path('password-reset/', views.password_reset_view, name='password_reset'), # Reset mot de passe
    # path('verify-email/<token>/', views.verify_email_view, name='verify_email'), # Vérification email
]