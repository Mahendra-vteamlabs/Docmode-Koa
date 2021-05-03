from django.contrib import admin
from .models import (
    extrafields,
    medical_councils,
    third_party_user_registration_log,
    states,
)
from lms.djangoapps.specialization.models import specializations


@admin.register(extrafields)
class ExtrafieldsAdmin(admin.ModelAdmin):
    readonly_fields = ("user",)
    list_display = [
        "user",
        "user_seo_url",
    ]
    # list_select_related = (
    #     'user',
    # )
    search_fields = ["user__email", "user_type"]


@admin.register(medical_councils)
class Medical_councilsAdmin(admin.ModelAdmin):

    list_display = [
        "council_name",
    ]
    search_fields = ["council_name"]


@admin.register(third_party_user_registration_log)
class Third_party_user_registration_logAdmin(admin.ModelAdmin):

    list_display = [
        "email",
        "status",
    ]
    search_fields = ["email"]


@admin.register(states)
class States_Admin(admin.ModelAdmin):

    list_display = [
        "name",
    ]
    search_fields = ["name"]
