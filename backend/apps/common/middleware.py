"""
apps/common/middleware.py
=========================
Site-wide middleware for the common app.

ForceCsrfCookieMiddleware
-------------------------
The cookie-consent banner lives in `base.html`, so it appears on EVERY page —
including pages without a form (home, about...). Its JavaScript posts to
`/consent/set/` and sends the CSRF token read from the `csrftoken` cookie.

Problem: Django only sets the `csrftoken` cookie when a page actually uses the
token (e.g. via `{% csrf_token %}` in a form). On a form-less page, the cookie
is missing → the fetch sends an empty token → Django answers 403 → the banner
never disappears.

Fix: call `get_token(request)` on every request. This makes Django attach the
`csrftoken` cookie to the response site-wide, so the banner's fetch always has a
valid token. This is safe: the CSRF cookie is designed to be readable by JS
(CSRF_COOKIE_HTTPONLY = False) and is NOT a secret on its own.
"""

from django.middleware.csrf import get_token


class ForceCsrfCookieMiddleware:
    """Ensure the `csrftoken` cookie is present on every response."""

    def __init__(self, get_response):
        # Django calls this once at startup and hands us the next callable
        # in the middleware chain.
        self.get_response = get_response

    def __call__(self, request):
        # Force Django to prepare the CSRF token for THIS request. The actual
        # Set-Cookie header is emitted by Django's CsrfViewMiddleware when it
        # builds the response.
        get_token(request)
        # Continue down the chain (other middleware + the view) and return the
        # response unchanged.
        return self.get_response(request)
