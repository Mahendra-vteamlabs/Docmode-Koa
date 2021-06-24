from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from django.db import transaction
from .models import (
    ProgramAdd,
    CustomCourseOverview,
    ProgramEnrollment,
    ProgramOrder,
    ProgramCoupon,
    CouponRadeemedDetails,
    ProgramCertificate_Template,
    ProgramCouponRemainUsage,
)


class CustomCourseOverviewAdmin(admin.ModelAdmin):
    """ Admin Interface for Role model. """

    list_display = ["name"]


admin.site.register(CustomCourseOverview, CustomCourseOverviewAdmin)


class ProgramAddAdmin(admin.ModelAdmin):
    """ Admin Interface for Role model. """

    list_display = ["name", "price"]


admin.site.register(ProgramAdd, ProgramAddAdmin)


class ProgramEnrollmentAdmin(admin.ModelAdmin):
    """ Admin Interface for Role model. """

    list_display = ["user", "program"]


admin.site.register(ProgramEnrollment, ProgramEnrollmentAdmin)


class ProgramOrderAdmin(admin.ModelAdmin):
    """ Admin Interface for Role model. """

    # raw_id_fields = ('user',)
    list_display = ["user", "program", "status"]


admin.site.register(ProgramOrder, ProgramOrderAdmin)


class ProgramCouponAdmin(admin.ModelAdmin):
    """ Admin Interface for Role model. """

    list_display = ["program", "coupon_code", "is_active"]


admin.site.register(ProgramCoupon, ProgramCouponAdmin)


class CouponRadeemedDetailsAdmin(admin.ModelAdmin):
    """ Admin Interface for Role model. """

    # raw_id_fields = ('user')
    list_display = ["user", "program", "coupon", "status"]
    readonly_fields = ("user",)


admin.site.register(CouponRadeemedDetails, CouponRadeemedDetailsAdmin)


class ProgramCertificate_TemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "program", "is_active"]


admin.site.register(ProgramCertificate_Template, ProgramCertificate_TemplateAdmin)
admin.site.register(ProgramCouponRemainUsage)
