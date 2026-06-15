"""Custom template filters shared across apps."""

from django import template
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
