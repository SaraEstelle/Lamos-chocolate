"""
apps/main/urls.py
=================
Routes de l'app principale (homepage, about, pages statiques).

Contenu :
- Homepage (/)
- À propos (about)
- Politique de confidentialité (privacy)
- Conditions d'utilisation (terms)
- Contact (contact)
- Blog (optionnel)

Cette app ne nécessite pas d'authentification.
"""

from django.urls import path

# Nom de cette app (utilisé dans les templates avec {% url 'main:home' %})
app_name = 'main'

# Routes de cette app
# Les vraies routes seront ajoutées dans feature/frontend-ui
urlpatterns = [
    # path('', views.home_view, name='home'),              # Homepage
    # path('about/', views.about_view, name='about'),      # À propos
    # path('privacy/', views.privacy_view, name='privacy'),# Politique de confidentialité
    # path('terms/', views.terms_view, name='terms'),      # Conditions d'utilisation
    # path('contact/', views.contact_view, name='contact'),# Formulaire de contact
]