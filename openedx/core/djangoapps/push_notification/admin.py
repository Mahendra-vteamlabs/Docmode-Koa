from django.contrib import admin

from .models import (
    DocmodeNotificationMessage,
    DocmodeNotification,
    MobileDiviseDetail,
    DocmodeNotificationCourse,
    DocmodeNotificationEmail,
)


class DocmodeNotificationMessageAdmin(admin.ModelAdmin):
    list_display = ["title", "message"]
    search_fields = ["title", "message"]
    readonly_fields = ["created", "modified"]
    exclude = (
        "created",
        "modified",
    )


class DocmodeNotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "message", "redirection_type", "status", "scheduled_time"]
    search_fields = ["title"]
    exclude = (
        "created",
        "modified",
    )


class DocmodeNotificationCourseAdmin(admin.ModelAdmin):
    list_display = ["course_id", "redirection_type", "status", "scheduled_time"]
    search_fields = ["course_id"]
    exclude = (
        "created",
        "modified",
    )


class MobileDiviseDetailAdmin(admin.ModelAdmin):
    search_fields = ["user"]
    exclude = (
        "created",
        "modified",
    )

    def has_add_permission(self, request, obj=None):
        return False


class DocmodeNotificationEmailAdmin(admin.ModelAdmin):
    list_display = ["course_id", "redirection_type", "status", "scheduled_time"]
    filter_horizontal = ("users",)
    exclude = (
        "created",
        "modified",
    )


admin.site.register(DocmodeNotificationMessage, DocmodeNotificationMessageAdmin)
admin.site.register(MobileDiviseDetail, MobileDiviseDetailAdmin)
admin.site.register(DocmodeNotification, DocmodeNotificationAdmin)
admin.site.register(DocmodeNotificationCourse, DocmodeNotificationCourseAdmin)
admin.site.register(DocmodeNotificationEmail, DocmodeNotificationEmailAdmin)
