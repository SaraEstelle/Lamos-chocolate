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
- /fr/cart/add/         → Panier, préfixé i18n (double mode form POST / AJAX)
- /checkout/webhook/    → Stripe webhook (pas de langue)
- /admin/               → Django Admin (pas de langue)

Règulation Suisse (RGPD) :
- Pas de tracking sans consentement
- Cookies sécurisés (SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE)
- Droit d'accès aux données
"""

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static

# ============================================================================
# ROUTES AVEC SUPPORT i18n (FR/EN/DE/IT)
# Ces routes seront accessibles en /fr/, /en/, /de/, /it/
# ============================================================================
i18n_urlpatterns = [
    # =========================================================================
    # App principale — homepage, about, brand story, pages statiques
    # =========================================================================
    path("", include("apps.main.urls", namespace="main")),

    # =========================================================================
    # Catalogue produits — listing, détail produit, filtres
    # =========================================================================
    path("shop/", include("apps.shop.urls", namespace="shop")),

    # =========================================================================
    # Panier — ajouter/retirer articles, voir le panier
    # =========================================================================
    path("cart/", include("apps.cart.urls", namespace="cart")),

    # =========================================================================
    # Paiement — checkout, confirmation, intégration Stripe
    # =========================================================================
    path("checkout/", include("apps.checkout.urls", namespace="checkout")),

    # =========================================================================
    # Authentification client — login, register, reset password
    # =========================================================================
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),

    # =========================================================================
    # Espace client — mon compte, historique commandes, adresses
    # =========================================================================
    path("my-account/", include("apps.customer_area.urls", namespace="customer_area")),

    # =========================================================================
    # Portail B2B — formulaire corporate, demande de devis
    # =========================================================================
    path("b2b/", include("apps.b2b.urls", namespace="b2b")),

    # ========================================================================
    # Login Google (social login accounts)
    # =======================================================================
    path("accounts/social/", include("allauth.urls")),
]

# ============================================================================
# ROUTES SANS i18n (pas de préfixe /fr/ ou /en/)
# Ces routes ne supportent qu'une seule langue globale
# ============================================================================
urlpatterns = [
    # =========================================================================
    # Django Admin — interface d'administration (réservé aux superusers)
    # /admin/login, /admin/users, /admin/products, etc.
    # =========================================================================
    path("admin/", admin.site.urls),

    # =========================================================================
    # Webhook Stripe — réception des paiements (requête POST raw de Stripe)
    # ⚠️ IMPORTANT : sans CSRF car Stripe envoie une requête raw
    # Cette route traite les événements payment_intent.succeeded, etc.
    # =========================================================================
    path("checkout/webhook/", include("apps.checkout.urls_webhook")),

    # =========================================================================
    # Admin personnalisé — tableau de bord, gestion produits, stocks
    # Accessible seulement aux staff/superusers
    # =========================================================================
    path("backoffice/", include("apps.backoffice.urls", namespace="backoffice")),

    # =========================================================================
    # Cockpit exécutif — couche décisionnelle standalone (PRD §8)
    # Réservé au staff ; distinct du backoffice OPS et du site public.
    # =========================================================================
    path("cockpit/", include("apps.cockpit.urls", namespace="cockpit")),

    # =========================================================================
    # Sélecteur de langue — formulaire Django pour changer la langue
    # POST vers /i18n/setlang/ avec next=URL_retour
    # =========================================================================
    path("i18n/", include("django.conf.urls.i18n")),
]

# ============================================================================
# AJOUTER LES ROUTES i18n AVEC PRÉFIXE /fr/, /en/, /de-ch/, /it-ch/
# ============================================================================
# Cette fonction Django ajoute automatiquement les préfixes de langue
# devant les routes i18n_urlpatterns
#
# prefix_default_language=False :
# - Ne pas créer de routes dupliquées
# - Sans ça : /shop/, /fr/shop/, /en/shop/
# - Avec ça : /fr/shop/, /en/shop/ seulement
urlpatterns += i18n_patterns(
    *i18n_urlpatterns,
    prefix_default_language=False,
)

# ============================================================================
# PAGES D'ERREUR PERSONNALISÉES
# ============================================================================
# Remplacer les pages d'erreur Django par des pages custom
# Elles doivent être définies dans apps.main.views
#
# Exemple : si un utilisateur accède à /invalid-path/,
# Django appelle handler404 qui affiche une page custom 404.html
# ============================================================================
# handler404 = "apps.main.views.page_not_found"          # 404 - Page non trouvée
# handler500 = "apps.main.views.server_error"            # 500 - Erreur serveur
# handler403 = "apps.main.views.permission_denied"       # 403 - Accès refusé

# ============================================================================
# FICHIERS STATIQUES ET MÉDIA (images, uploads, CSS, JS)
# ============================================================================
# En développement seulement (en production, Nginx/S3 s'en charge)
#
# STATIC_URL = '/static/' → CSS, JS, images du site (ne changent pas)
# MEDIA_URL = '/media/' → uploads utilisateur (avatars, documents)
# ============================================================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ============================================================================
# DJANGO DEBUG TOOLBAR — route /__debug__/ (dev only)
# ============================================================================
# Enabled only when the app is installed (dev settings), so it stays inert
# in production where debug_toolbar is absent from INSTALLED_APPS.
if "debug_toolbar" in settings.INSTALLED_APPS:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
