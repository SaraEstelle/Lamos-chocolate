"""Custom template filters shared across apps."""

from django import template
from django.urls import translate_url
from django.utils.translation import get_language

register = template.Library()


@register.filter
def localized(obj: object, field_name: str) -> str:
    """Return a bilingual model field for the active language.

    Models expose paired fields such as ``name_fr`` / ``name_en``. This filter
    picks the right one from the active language, falling back to French.

    Args:
        obj: A model instance exposing ``<field_name>_fr`` / ``<field_name>_en``.
        field_name: Base name of the bilingual field (e.g. ``"name"``).

    Returns:
        The field value for the active language, or an empty string.

    Usage:
        ``{{ product|localized:"name" }}``
    """
    lang = (get_language() or "fr")[:2]
    suffix = "en" if lang == "en" else "fr"
    return getattr(obj, f"{field_name}_{suffix}", "")


@register.simple_tag(takes_context=True)
def switch_language_url(context, target_lang):
    """Return the CURRENT page's URL translated into ``target_lang``.

    WHY THIS EXISTS
    ---------------
    With ``prefix_default_language=False`` the default language (fr) has NO
    URL prefix ("/") while the others do ("/en/", "/de-ch/", "/it-ch/").

    Django's built-in ``set_language`` view tries to translate the ``next``
    URL for us, but it re-resolves that URL using the language that is ACTIVE
    during the POST to ``/i18n/setlang/`` (read from the cookie). Once the
    cookie holds a prefix-less language (fr), a prefixed path like "/en/"
    can no longer be resolved, the translation silently fails, and the view
    redirects to the untranslated URL -> the language never changes.

    THE FIX
    -------
    Compute the target URL HERE, at TEMPLATE RENDER time. While a page is
    rendering, the active language always matches the page's own prefix, so
    ``translate_url`` resolves the current path and reverses it in the target
    language reliably. We hand that ready-made URL to the form's ``next``
    field, so ``set_language`` only has to set the cookie and redirect.

    Usage in a template:
        {% switch_language_url "fr" as fr_url %}
        <input type="hidden" name="next" value="{{ fr_url }}">
    """
    request = context["request"]
    # get_full_path() keeps any query string (?category=..., ?page=2, ...).
    return translate_url(request.get_full_path(), target_lang)
