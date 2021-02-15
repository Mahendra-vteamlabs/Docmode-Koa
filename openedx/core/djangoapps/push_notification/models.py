# -*- coding: utf-8 -*-
import logging

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from model_utils.models import TimeStampedModel

from opaque_keys.edx.django.models import CourseKeyField

log = logging.getLogger(__name__)

NOTIFICATION_REDIRECTION_TYPE_CHOICES = (
    ("disscussion", "Disscussion"),
    ("email_digest", "Email Digest"),
    ("instructor", "Instructor Communication"),
    ("recuring_nudge", "Recuring Nudge"),
    ("start_date", "start Date"),
    ("before_days", "Before Days"),
    ("course_created", "Course Created"),
)


STATUS_TYPE_CHOICES = (
    ("draft", "Draft"),
    ("running", "Running"),
    ("error", "Error"),
    ("sent", "Sent"),
)


class DocmodeNotificationMessage(TimeStampedModel):
    title = models.CharField(_("Title"), max_length=100)
    message = models.TextField(_("Message"), blank=True, null=True, max_length=255)
    redirection_type = models.CharField(
        ("Redirection"),
        max_length=255,
        choices=NOTIFICATION_REDIRECTION_TYPE_CHOICES,
        default="start_date",
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Notification Message"


class DocmodeNotification(TimeStampedModel):

    title = models.CharField(_("Title"), max_length=100)
    message = models.TextField(_("Message"), blank=True, null=True, max_length=255)
    redirection_type = models.CharField(
        ("Redirection"),
        max_length=255,
        choices=NOTIFICATION_REDIRECTION_TYPE_CHOICES,
        default="start_date",
    )
    status = models.CharField(
        ("Status"), max_length=10, choices=STATUS_TYPE_CHOICES, default="begin"
    )
    users = models.ForeignKey(
        User, db_index=True, blank=True, null=True, on_delete=models.CASCADE
    )

    scheduled_time = models.DateTimeField(blank=True, null=True)

    course_id = CourseKeyField(max_length=255, db_index=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Notifications"


class DocmodeNotificationCourse(TimeStampedModel):

    redirection_type = models.CharField(
        ("Redirection"),
        max_length=255,
        choices=NOTIFICATION_REDIRECTION_TYPE_CHOICES,
        default="start_date",
    )
    status = models.CharField(
        ("Status"), max_length=10, choices=STATUS_TYPE_CHOICES, default="begin"
    )

    scheduled_time = models.DateTimeField(blank=True, null=True)

    course_id = CourseKeyField(max_length=255, db_index=True, null=True)

    def __str__(self):
        return str(self.course_id)

    class Meta:
        verbose_name = "NotificationsCourse"


class DocmodeNotificationEmail(TimeStampedModel):

    redirection_type = models.CharField(
        ("Redirection"),
        max_length=255,
        choices=NOTIFICATION_REDIRECTION_TYPE_CHOICES,
        default="start_date",
    )
    status = models.CharField(
        ("Status"), max_length=10, choices=STATUS_TYPE_CHOICES, default="begin"
    )
    users = models.ManyToManyField(User, db_index=True)

    scheduled_time = models.DateTimeField(blank=True, null=True)

    course_id = CourseKeyField(max_length=255, db_index=True, null=True)

    def __str__(self):
        return str(self.course_id)

    class Meta:
        verbose_name = "NotificationsEmail"


class MobileDiviseDetail(TimeStampedModel):

    user = models.ForeignKey(
        User, db_index=True, related_name="mobile", on_delete=models.CASCADE
    )
    mobile_device_token = models.CharField(blank=True, null=True, max_length=3000)
    mobile_device_id = models.CharField(blank=True, null=True, max_length=3000)
    mobile_version = models.CharField(blank=True, null=True, max_length=3000)
    mobile_device_type = models.CharField(blank=True, null=True, max_length=3000)

    def __str__(self):
        return self.mobile_device_type

    class Meta:
        verbose_name = "MobileDiviseDetail"
