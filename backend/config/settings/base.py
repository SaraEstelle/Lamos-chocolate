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

# -------------------------------------------------------------------
# Applications
# -------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# -------------------------------------------------------------------
# Middleware
# -------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# -------------------------------------------------------------------
# URLs
# -------------------------------------------------------------------

ROOT_URLCONF = "config.urls"

# -------------------------------------------------------------------
# Templates
# -------------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
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

# -------------------------------------------------------------------
# Internationalization
# -------------------------------------------------------------------

LANGUAGE_CODE = env(
    "LANGUAGE_CODE",
    default="fr"
)

TIME_ZONE = env(
    "TIME_ZONE",
    default="Europe/Paris"
)

USE_I18N = True

USE_TZ = True

# -------------------------------------------------------------------
# Static files
# -------------------------------------------------------------------

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

# -------------------------------------------------------------------
# Media files
# -------------------------------------------------------------------

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"

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