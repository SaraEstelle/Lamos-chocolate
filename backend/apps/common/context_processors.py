from django.conf import settings
def feature_flags(request):
    fb = settings.SOCIALACCOUNT_PROVIDERS.get("facebook", {}).get("APP", {})
    return {"FACEBOOK_ENABLED": bool(fb.get("client_id"))}