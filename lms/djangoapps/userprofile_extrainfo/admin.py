# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import (
    education,
    awards,
    research_papers,
    media_featured,
    clinic_hospital_address,
    healthcare_awareness_videos,
    experience,
)

# Register your models here.


class education_admin(admin.ModelAdmin):
    raw_id_fields = [
        "user",
        "year",
    ]
    search_fields = ["user", "year"]


admin.site.register(education)


class awards_admin(admin.ModelAdmin):
    raw_id_fields = [
        "user",
        "year",
    ]
    search_fields = ["user", "year"]


admin.site.register(awards)


class research_papers_admin(admin.ModelAdmin):
    raw_id_fields = [
        "user",
        "title",
    ]
    search_fields = ["user", "title"]


admin.site.register(research_papers)


class media_featured_admin(admin.ModelAdmin):
    raw_id_fields = [
        "user",
        "title",
    ]
    search_fields = ["user", "title"]


admin.site.register(media_featured)


class clinic_hospital_address_admin(admin.ModelAdmin):
    raw_id_fields = [
        "user",
        "clinic_hospital_name",
    ]
    search_fields = ["user", "clinic_hospital_name"]


admin.site.register(clinic_hospital_address)


class healthcare_awareness_videos_admin(admin.ModelAdmin):
    raw_id_fields = [
        "user",
        "clinic_hospital_name",
    ]
    search_fields = ["user", "clinic_hospital_name"]


admin.site.register(healthcare_awareness_videos)


class experience_admin(admin.ModelAdmin):
    raw_id_fields = [
        "user",
        "year",
    ]
    search_fields = ["user", "year"]


admin.site.register(experience)
