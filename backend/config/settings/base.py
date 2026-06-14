import os
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
]

LOCAL_APPS = [
    "apps.common",
    "apps.main",
    "apps.accounts",
    "apps.shop",
    "apps.cart",
    "apps.checkout",
    "apps.customer_area",
    "apps.b2b",
    "apps.backoffice",
    "apps.forecasting",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

# ============================================================================
# AUTH — Custom user model
# ============================================================================
# Customer replaces Django's default User model. Must be set BEFORE the first
# migration that references settings.AUTH_USER_MODEL (accounts.PasswordResetToken).
AUTH_USER_MODEL = "accounts.Customer"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", default="lamos_chocolate"),
        "USER": config("POSTGRES_USER", default="postgres"),
        "PASSWORD": config("POSTGRES_PASSWORD", default="postgres"),
        "HOST": config("POSTGRES_HOST", default="localhost"),
        "PORT": config("POSTGRES_PORT", default="5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation." "MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation." "CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation." "NumericPasswordValidator",
    },
]

LANGUAGE_CODE = config("LANGUAGE_CODE", default="fr")

TIME_ZONE = config("TIME_ZONE", default="Europe/Paris")

LANGUAGES = [
    ("fr", "Français"),
    ("en", "English"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

USE_I18N = True

USE_TZ = True

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Email ---
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@lamos-chocolate.ch")

SITE_URL = config("SITE_URL", default="http://localhost:8000")

# --- Stripe ---
STRIPE_PUBLIC_KEY = config("STRIPE_PUBLIC_KEY", default="")
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET", default="")

# --- Logging ---
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{levelname}] {asctime} | {name} | {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "verbose": {
            "format": (
                "[{levelname}] {asctime} | {name} | "
                "{filename}:{lineno} | {funcName}() | {message}"
            ),
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
        },
        "file_error": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGS_DIR, "django_errors.log"),
            "maxBytes": 10_485_760,
            "backupCount": 10,
            "level": "ERROR",
            "formatter": "verbose",
        },
        "file_all": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGS_DIR, "django.log"),
            "maxBytes": 10_485_760,
            "backupCount": 10,
            "level": "DEBUG",
            "formatter": "verbose",
        },
        "file_access": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOGS_DIR, "access.log"),
            "maxBytes": 10_485_760,
            "backupCount": 5,
            "level": "INFO",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file_all", "file_error"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file_access", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "file_all", "file_error"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file_all", "file_error"],
        "level": "INFO",
    },
}
