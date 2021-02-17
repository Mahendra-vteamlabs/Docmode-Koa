""" Django admin pages for organization models """
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from common.djangoapps.organizations.models import (
    Organization,
    OrganizationCourse,
    SponsoringCompany,
    OrganizationSlider,
    OrgShortCode,
    OrganizationMembers,
    Organization_sub_admins,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """ Admin for the Organization model. """

    actions = ["activate_selected", "deactivate_selected"]
    list_display = (
        "name",
        "short_name",
        "logo",
        "active",
        "marketing_display",
    )
    list_filter = ("active",)
    ordering = (
        "name",
        "short_name",
    )
    readonly_fields = ("created",)
    search_fields = (
        "name",
        "short_name",
    )

    def get_actions(self, request):
        actions = super(OrganizationAdmin, self).get_actions(request)

        # Remove the delete action.
        del actions["delete_selected"]

        return actions

    def activate_selected(self, request, queryset):
        """ Activate the selected entries. """
        queryset.update(active=True)
        count = queryset.count()

        if count == 1:
            message = _("1 organization entry was successfully activated")
        else:
            message = _("{count} organization entries were successfully activated")
            message.format(count=count)  # pylint: disable=no-member

        self.message_user(request, message)

    def deactivate_selected(self, request, queryset):
        """ Deactivate the selected entries. """
        queryset.update(active=False)
        count = queryset.count()

        if count == 1:
            message = _("1 organization entry was successfully deactivated")
        else:
            message = _("{count} organization entries were successfully deactivated")
            message.format(count=count)  # pylint: disable=no-member

        self.message_user(request, message)

    deactivate_selected.short_description = _("Deactivate selected entries")
    activate_selected.short_description = _("Activate selected entries")


@admin.register(OrganizationCourse)
class OrganizationCourseAdmin(admin.ModelAdmin):
    """ Admin for the CourseOrganization model. """

    list_display = ("course_id", "organization", "active")
    ordering = (
        "course_id",
        "organization__name",
    )
    search_fields = (
        "course_id",
        "organization__name",
        "organization__short_name",
    )

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        # Only display active Organizations.
        if db_field.name == "organization":
            kwargs["queryset"] = Organization.objects.filter(active=True).order_by(
                "name"
            )

        return super(OrganizationCourseAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )


@admin.register(SponsoringCompany)
class SponsoringCompanyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "short_name",
        "description",
        "logo_url",
        "created",
        "active",
    )
    readonly_fields = ("created",)
    ordering = ["created"]
    actions = ["activate_selected", "deactivate_selected"]

    def get_actions(self, request):
        """ return actions """
        actions = super(SponsoringCompanyAdmin, self).get_actions(request)
        del actions["delete_selected"]
        return actions

    def activate_selected(self, request, queryset):
        """activate the selected entries"""
        queryset.update(active=True)
        if queryset.count() == 1:
            message_bit = "1 organization entry was"
        else:
            message_bit = "%s organization entries were" % queryset.count()
        self.message_user(request, "%s successfully activated." % message_bit)

    def deactivate_selected(self, request, queryset):
        """deactivate the selected entries"""
        queryset.update(active=False)
        if queryset.count() == 1:
            message_bit = "1 organization entry was"
        else:
            message_bit = "%s organization entries were" % queryset.count()
        self.message_user(request, "%s successfully deactivated." % message_bit)

    deactivate_selected.short_description = "Deactivate s selected entries"
    activate_selected.short_description = "Activate s selected entries"


@admin.register(OrganizationSlider)
class OrganizationSliderAdmin(admin.ModelAdmin):
    list_display = ("organization", "image_s3_urls", "active")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        list down the active organizations
        """
        if db_field.name == "organization":
            kwargs["queryset"] = Organization.objects.filter(active=True)

        return super(OrganizationSliderAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )


@admin.register(OrgShortCode)
class OrgShortCodeAdmin(admin.ModelAdmin):
    list_display = ("organization", "code")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        list down the active organizations
        """
        if db_field.name == "organization":
            kwargs["queryset"] = Organization.objects.filter(active=True)

        return super(OrgShortCodeAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )


@admin.register(OrganizationMembers)
class OrganizationMembersAdmin(admin.ModelAdmin):
    list_display = ("user_id", "user_email", "organization", "is_admin")
    search_fields = ("user_email",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        list down the active organizations
        """
        if db_field.name == "organization":
            kwargs["queryset"] = Organization.objects.filter(active=True)

        return super(OrganizationMembersAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )


@admin.register(Organization_sub_admins)
class Organization_sub_admin_Admin(admin.ModelAdmin):
    list_display = ("user_email", "organization", "is_admin")
    search_fields = ("user_email",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        list down the active organizations
        """
        if db_field.name == "organization":
            kwargs["queryset"] = Organization.objects.filter(active=True)

        return super(Organization_sub_admin_Admin, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )
