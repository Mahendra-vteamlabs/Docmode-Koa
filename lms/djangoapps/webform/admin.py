from django.contrib import admin
from .models import webform


@admin.register(webform)
class WebAdmin(admin.ModelAdmin):

    list_display = ["courseid", "name", "location", "question"]

    search_fields = ["courseid"]
