from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")

DEBUG = config(
    "DEBUG",
    default=False,
    cast=bool
)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost",
    cast=lambda value: [
        host.strip()
        for host in value.split(",")
    ]
)

INSTALLED_APPS = []

MIDDLEWARE = []

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"

ASGI_APPLICATION = "config.asgi.application"

LANGUAGE_CODE = config(
    "LANGUAGE_CODE",
    default="fr"
)

TIME_ZONE = config(
    "TIME_ZONE",
    default="Europe/Paris"
)

USE_I18N = True

USE_TZ = True

STATIC_URL = "/static/"

MEDIA_URL = "/media/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
