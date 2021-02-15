from django.contrib import admin
from .models import extrafields
from lms.djangoapps.specialization.models import specializations


@admin.register(extrafields)
class ExtrafieldsAdmin(admin.ModelAdmin):

    list_display = [
        "user",
        "user_seo_url",
    ]
    search_fields = ["user__email", "user_type"]
