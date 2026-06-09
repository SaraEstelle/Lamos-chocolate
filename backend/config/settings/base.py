from pathlib import Path

import environ

# -------------------------------------------------------------------
# Base directory
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# -------------------------------------------------------------------
# Environment variables
# -------------------------------------------------------------------

env = environ.Env()

environ.Env.read_env()

# -------------------------------------------------------------------
# Security
# -------------------------------------------------------------------

SECRET_KEY = env(
    "SECRET_KEY",
    default="change-me"
)

DEBUG = env.bool(
    "DEBUG",
    default=False
)

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=["localhost"]
)

# ============================================================================
# INSTALLED_APPS — Toutes les apps Django utilisées
# ============================================================================
#
# Qu'est-ce qu'une app Django ?
# C'est un module réutilisable contenant models, views, urls, etc.
#
# Il y a 3 types :
# 1. Apps Django core (admin, auth, contenttypes, etc.)
# 2. Apps tierces (django-environ, django-rest-framework, etc.)
# 3. Apps personnalisées de Lamos (shop, accounts, cart, etc.)
# ============================================================================

INSTALLED_APPS = [
    # =========================================================================
    # 1. APPS DJANGO CORE — Ne pas supprimer
    # =========================================================================
    "django.contrib.admin",              # Interface admin /admin/
    "django.contrib.auth",               # Authentification et permissions
    "django.contrib.contenttypes",       # Framework pour les modèles
    "django.contrib.sessions",           # Gestion des sessions utilisateur
    "django.contrib.messages",           # Messages flash (notifications)
    "django.contrib.staticfiles",        # Gestion des CSS, JS, images

    # =========================================================================
    # 2. APPS TIERCES — Bibliothèques externes
    # =========================================================================
    "django_extensions",                 # Commandes admin utiles
    "rest_framework",                    # API REST (optionnel mais installé)

    # =========================================================================
    # 3. APPS PERSONNALISÉES DE LAMOS
    # =========================================================================
    # App commune — utilitaires, middlewares, permissions
    "apps.common",

    # App principale — homepage, about, brand story
    "apps.main",

    # Authentification — login, register, reset password
    "apps.accounts",

    # Catalogue produits
    "apps.shop",

    # Panier et gestion de session
    "apps.cart",

    # Paiement et commandes
    "apps.checkout",

    # Espace client — mon compte, historique commandes
    "apps.customer_area",

    # Portail B2B — formulaire corporate
    "apps.b2b",

    # Admin personnalisé — tableau de bord, gestion produits
    "apps.backoffice",

    # Prévisions de ventes et alertes
    "apps.forecasting",
]


# ============================================================================
# MIDDLEWARE — Traitement des requêtes/réponses (ordre IMPORTANT)
# ============================================================================
#
# Middleware = fonction qui intercepte chaque requête HTTP.
# Ordre d'exécution = ordre de la liste (de haut en bas pour requête,
# de bas en haut pour réponse)
# ============================================================================

MIDDLEWARE = [
    # 1. Sécurité — force HTTPS, headers de sécurité
    "django.middleware.security.SecurityMiddleware",

    # 2. Sessions — stockage des données utilisateur (panier, auth)
    "django.contrib.sessions.middleware.SessionMiddleware",

    # 3. ⭐ LOCALE/i18n — détecte la langue (FR/EN) demandée
    #    IMPORTANT : doit être après SessionMiddleware, avant CommonMiddleware
    "django.middleware.locale.LocaleMiddleware",

    # 4. Commun — traitement basique (gzip, compression)
    "django.middleware.common.CommonMiddleware",

    # 5. CSRF — protection contre les attaques cross-site request forgery
    "django.middleware.csrf.CsrfViewMiddleware",

    # 6. Auth — associe l'utilisateur à la requête
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    # 7. Messages — système de notifications (flash messages)
    "django.contrib.messages.middleware.MessageMiddleware",

    # 8. Clickjacking — protection contre les iframes malveillantes
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # 9. Custom — nos propres middlewares (logging, monitoring)
    "apps.common.middleware.RequestLoggingMiddleware",
]

# -------------------------------------------------------------------
# URLs
# -------------------------------------------------------------------

ROOT_URLCONF = "config.urls"

# ============================================================================
# TEMPLATES — Configuration du moteur de templates Django
# ============================================================================
#
# Un template = fichier HTML avec variables {{ variable }} et boucles
# ============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # Où chercher les templates (.html)
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),  # backend/templates/
        ],

        'APP_DIRS': True,  # Chercher aussi dans apps/*/templates/

        # Context processors — variables disponibles dans TOUS les templates
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # ⭐ i18n — variables {{ LANGUAGE_CODE }} dans les templates
                'django.template.context_processors.i18n',

                # Média URL — {{ MEDIA_URL }} pour afficher les images
                'django.template.context_processors.media',

                # Static URL — {{ STATIC_URL }} pour CSS, JS
                'django.template.context_processors.static',
            ],
        },
    },
]

# -------------------------------------------------------------------
# WSGI / ASGI
# -------------------------------------------------------------------

WSGI_APPLICATION = "config.wsgi.application"

ASGI_APPLICATION = "config.asgi.application"

# -------------------------------------------------------------------
# Database
# -------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env(
            "DB_NAME",
            default="lamos_chocolate"
        ),
        "USER": env(
            "DB_USER",
            default="postgres"
        ),
        "PASSWORD": env(
            "DB_PASSWORD",
            default="postgres"
        ),
        "HOST": env(
            "DB_HOST",
            default="localhost"
        ),
        "PORT": env(
            "DB_PORT",
            default="5432"
        ),
    }
}

# ============================================================================
# INTERNATIONALIZATION (i18n) — Support multilingue FR/EN
# ============================================================================
#
# Configuration pour avoir un site en 2 langues : Français et Anglais
# Les URLs seront automatiquement en /fr/ ou /en/
# ============================================================================

# Langue par défaut si le navigateur n'en demande pas une
LANGUAGE_CODE = env(
    "LANGUAGE_CODE",
    default="fr",  # Défaut = français
)

# Fuseau horaire par défaut
TIME_ZONE = env(
    "TIME_ZONE",
    default="Europe/Paris",  # Zone horaire Suisse/France
)

# Activer l'internationalisation
USE_I18N = True

# Activer les fuseaux horaires (stockage en UTC en DB)
USE_TZ = True

# Dossier où sont les fichiers de traduction (.po, .mo)
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),  # backend/locale/fr/, backend/locale/en/
]

# ⭐ LANGUES SUPPORTÉES — Définir les langues du site
LANGUAGES = [
    ('fr', 'Français'),     # Code langue, Nom affiché
    ('en', 'English'),      # Pour sélecteur de langue
    ('it-ch', 'Italiano (Svizzera)'),
    ('de-ch', 'Deutsch (Schweiz)'),
]

# ============================================================================
# AUTHENTIFICATION — Modèle utilisateur personnalisé
# ============================================================================
#
# Par défaut Django utilise User. On utilise Customer à la place.
# ============================================================================

AUTH_USER_MODEL = 'accounts.Customer'  # Notre modèle Customer

# ============================================================================
# FICHIERS STATIQUES ET MÉDIA
# ============================================================================
#
# Statiques = CSS, JS, images du site (ne changent pas)
# Média = uploads utilisateur (avatar, documents, etc.)
# ============================================================================

# URL publique pour accéder aux statiques
STATIC_URL = '/static/'

# Où stocker les statiques collectés
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Chemins additionnels où chercher les statiques
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # backend/static/
]

# URL publique pour accéder aux uploads média
MEDIA_URL = '/media/'

# Où stocker les fichiers uploadés
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# -------------------------------------------------------------------
# Default primary key
# -------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------------------------------------------
# Stripe
# -------------------------------------------------------------------

STRIPE_PUBLIC_KEY = env(
    "STRIPE_PUBLIC_KEY",
    default=""
)

STRIPE_SECRET_KEY = env(
    "STRIPE_SECRET_KEY",
    default=""
)

# ============================================================================
# LOGGING — Enregistrement des erreurs et événements
# ============================================================================
#
# Qu'est-ce que c'est ?
# Quand Django a un bug, au lieu juste d'afficher une erreur,
# on la sauvegarde dans un fichier logs/ pour analyse.
#
# Exemple :
# - 2026-06-09 15:42:31 ERROR | Exception in view checkout
# - Stack trace complet sauvegardé
# - Utile pour debug en production
# ============================================================================

import os

# Créer le dossier logs/ s'il n'existe pas
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    # Version du format de logging (ne pas toucher)
    'version': 1,

    # Ne pas hériter de la config Django par défaut
    'disable_existing_loggers': False,

    # =========================================================================
    # FORMATEURS — Comment afficher les logs
    # =========================================================================
    'formatters': {
        # Format court — pour la console en développement
        'simple': {
            'format': '[{levelname}] {asctime} | {name} | {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },

        # Format détaillé — pour les fichiers en production
        'verbose': {
            'format': (
                '[{levelname}] {asctime} | {name} | '
                '{filename}:{lineno} | {funcName}() | {message}'
            ),
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },

    # =========================================================================
    # HANDLERS — Où envoyer les logs (fichier ou console)
    # =========================================================================
    'handlers': {
        # Handler 1 : Afficher dans la console (pour le développement)
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
        },

        # Handler 2 : Sauvegarder les erreurs (CRITICAL, ERROR) dans un fichier
        'file_error': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'django_errors.log'),
            'maxBytes': 10_485_760,  # 10 MB — puis créer un nouveau fichier
            'backupCount': 10,       # Garder 10 anciens fichiers
            'level': 'ERROR',
            'formatter': 'verbose',
        },

        # Handler 3 : Sauvegarder TOUS les logs (DEBUG+) dans un fichier
        'file_all': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'django.log'),
            'maxBytes': 10_485_760,  # 10 MB
            'backupCount': 10,
            'level': 'DEBUG',
            'formatter': 'verbose',
        },

        # Handler 4 : Sauvegarder les requêtes HTTP dans un fichier (accès)
        'file_access': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'access.log'),
            'maxBytes': 10_485_760,
            'backupCount': 5,
            'level': 'INFO',
            'formatter': 'simple',
        },
    },

    # =========================================================================
    # LOGGERS — Qui envoie les logs, et vers où
    # =========================================================================
    'loggers': {
        # Logger 1 : Django core (config, middleware, db)
        'django': {
            'handlers': ['console', 'file_all', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },

        # Logger 2 : Accès HTTP (requêtes entrantes)
        'django.request': {
            'handlers': ['file_access', 'console'],
            'level': 'INFO',
            'propagate': False,
        },

        # Logger 3 : Base de données (requêtes SQL)
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },

        # Logger 4 : Nos apps personnalisées (apps/*)
        'apps': {
            'handlers': ['console', 'file_all', 'file_error'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },

    # =========================================================================
    # ROOT LOGGER — Fallback si un logger n'est pas défini
    # =========================================================================
    'root': {
        'handlers': ['console', 'file_all', 'file_error'],
        'level': 'INFO',
    },
}
