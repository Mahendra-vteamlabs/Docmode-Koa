from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin


from .models import user_session_tracking


@admin.register(user_session_tracking)
class user_session_tracking(admin.ModelAdmin):
    """Admin for course email."""

    list_display = [
        "course_id",
        "pagein",
        "pageout",
    ]
