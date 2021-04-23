from django.contrib import admin
from .models import course_extrainfo


@admin.register(course_extrainfo)
class Course_extrainfo_Admin(admin.ModelAdmin):

    list_display = [
        "course_id",
        "course_type",
        "specialization",
        "mci_mandatory",
        "google_calendar_url",
        "microsite_visibile_only",
    ]

    search_fields = ["course_id"]
