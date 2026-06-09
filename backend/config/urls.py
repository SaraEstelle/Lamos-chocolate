"""
config/urls.py
==============
Point d'entrée de TOUTES les routes de Lamos Chocolate.

Responsabilités :
1. Importer les routes de toutes les apps (shop, accounts, cart, etc.)
2. Configurer le support multilingue FR/EN via i18n_patterns
3. Gérer les routes publiques (webhook Stripe, health check)
4. Gérer les routes protégées (admin, backoffice)
5. Gérer les pages d'erreur personnalisées (404, 500)

Structure des URLs :
- /fr/shop/              → Routes en français
- /en/shop/             → Routes en anglais
- /api/cart/add/        → AJAX (pas de langue)
- /checkout/webhook/    → Stripe webhook (pas de langue)
- /admin/               → Django Admin (pas de langue)
"""

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static

# ============================================================================
# ROUTES AVEC SUPPORT i18n (FR/EN)
# Ces routes seront accessibles en /fr/ et /en/
# ============================================================================
i18n_urlpatterns = [
    # App principale (homepage, about, brand story)
    path("", include("apps.main.urls", namespace="main")),

    # Catalogue produits
    path("shop/", include("apps.shop.urls", namespace="shop")),

    # Panier
    path("cart/", include("apps.cart.urls", namespace="cart")),

    # Paiement Stripe
    path("checkout/", include("apps.checkout.urls", namespace="checkout")),

    # Authentification client (login, register, reset password)
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),

    # Espace client (mon compte, historique commandes)
    path("my-account/", include("apps.customer_area.urls", namespace="customer_area")),

    # Portail B2B (formulaire corporate)
    path("b2b/", include("apps.b2b.urls", namespace="b2b")),
]

# ============================================================================
# ROUTES SANS i18n (pas de préfixe /fr/ ou /en/)
# Ces routes ne supportent qu'une seule langue globale
# ============================================================================
urlpatterns = [
    # Django Admin (réservé aux superusers)
    path("admin/", admin.site.urls),

    # API AJAX (panier, cart add, etc.) - pas de langue car JSON
    path("api/", include("apps.cart.urls_api")),

    # Webhook Stripe (réception des paiements)
    # ⚠️ IMPORTANT : sans CSRF car Stripe envoie une requête raw
    path("checkout/webhook/", include("apps.checkout.urls_webhook")),

    # Admin personnalisé (tableau de bord, gestion produits, stocks)
    path("backoffice/", include("apps.backoffice.urls", namespace="backoffice")),

    # Sélection de langue (formulaire django.views.i18n.set_language)
    path("i18n/", include("django.conf.urls.i18n")),
]

# ============================================================================
# AJOUTER LES ROUTES i18n AVEC PRÉFIXE /fr/ et /en/
# ============================================================================
# Cette fonction Django ajoute automatiquement /fr/ et /en/ devant les routes
urlpatterns += i18n_patterns(
    *i18n_urlpatterns,
    prefix_default_language=False,  # Ne pas dupliquer les routes sans préfixe
)

# ============================================================================
# PAGES D'ERREUR PERSONNALISÉES
# ============================================================================
# Remplacer les pages d'erreur Django par des pages custom
handler404 = "apps.main.views.page_not_found"          # 404 - Page non trouvée
handler500 = "apps.main.views.server_error"            # 500 - Erreur serveur
handler403 = "apps.main.views.permission_denied"       # 403 - Accès refusé

# ============================================================================
# FICHIERS STATIQUES ET MÉDIA (images, uploads, CSS, JS)
# En développement seulement (en production, Nginx s'en charge)
# ============================================================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)