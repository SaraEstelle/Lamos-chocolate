from django.contrib import admin

from apps.analytics.models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "channel", "canton", "value_chf", "created_at")
    list_filter = ("event_type", "channel", "canton")
    date_hierarchy = "created_at"
    readonly_fields = ("id", "created_at")