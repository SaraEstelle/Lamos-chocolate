from .base import *  # noqa: F401,F403

DEBUG = True

EMAIL_BACKEND = (
    "django.core.mail.backends.console.EmailBackend"
)

INTERNAL_IPS = [
    "127.0.0.1",
]

# ============================================================================
# DJANGO DEBUG TOOLBAR (dev only)
# ============================================================================
# The package ships in requirements/dev.txt. We wire it up here so it never
# leaks into base/prod settings.
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405

# DebugToolbarMiddleware must run as early as possible, right after the
# security middleware, so it sees the final rendered response.
MIDDLEWARE.insert(  # noqa: F405
    1, "debug_toolbar.middleware.DebugToolbarMiddleware"
)


def show_toolbar(request):
    """Show the toolbar whenever DEBUG is on.

    The default INTERNAL_IPS check fails under Docker/WSL because the
    container's client IP is not 127.0.0.1. Gating on DEBUG is reliable here
    since this settings module is dev-only.
    """
    return DEBUG


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": "config.settings.dev.show_toolbar",
}
