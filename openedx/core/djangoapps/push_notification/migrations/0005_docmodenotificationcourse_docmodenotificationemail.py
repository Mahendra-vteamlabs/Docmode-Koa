# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-08-09 11:06
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.utils.timezone
import model_utils.fields
import opaque_keys.edx.django.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("push_notification", "0004_docmodenotification_users"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocmodeNotificationCourse",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                (
                    "redirection_type",
                    models.CharField(
                        choices=[
                            (b"disscussion", b"Disscussion"),
                            (b"email_digest", b"Email Digest"),
                            (b"instructor", b"Instructor Communication"),
                            (b"recuring_nudge", b"Recuring Nudge"),
                            (b"start_date", b"start Date"),
                            (b"before_days", b"Before Days"),
                            (b"course_created", b"Course Created"),
                        ],
                        default=b"start_date",
                        max_length=255,
                        verbose_name=b"Redirection",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            (b"draft", b"Draft"),
                            (b"running", b"Running"),
                            (b"error", b"Error"),
                            (b"sent", b"Sent"),
                        ],
                        default=b"begin",
                        max_length=10,
                        verbose_name=b"Status",
                    ),
                ),
                ("scheduled_time", models.DateTimeField(blank=True, null=True)),
                (
                    "course_id",
                    opaque_keys.edx.django.models.CourseKeyField(
                        db_index=True, max_length=255, null=True
                    ),
                ),
            ],
            options={
                "verbose_name": "NotificationsCourse",
            },
        ),
        migrations.CreateModel(
            name="DocmodeNotificationEmail",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                (
                    "redirection_type",
                    models.CharField(
                        choices=[
                            (b"disscussion", b"Disscussion"),
                            (b"email_digest", b"Email Digest"),
                            (b"instructor", b"Instructor Communication"),
                            (b"recuring_nudge", b"Recuring Nudge"),
                            (b"start_date", b"start Date"),
                            (b"before_days", b"Before Days"),
                            (b"course_created", b"Course Created"),
                        ],
                        default=b"start_date",
                        max_length=255,
                        verbose_name=b"Redirection",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            (b"draft", b"Draft"),
                            (b"running", b"Running"),
                            (b"error", b"Error"),
                            (b"sent", b"Sent"),
                        ],
                        default=b"begin",
                        max_length=10,
                        verbose_name=b"Status",
                    ),
                ),
                ("scheduled_time", models.DateTimeField(blank=True, null=True)),
                (
                    "course_id",
                    opaque_keys.edx.django.models.CourseKeyField(
                        db_index=True, max_length=255, null=True
                    ),
                ),
                (
                    "users",
                    models.ManyToManyField(db_index=True, to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "verbose_name": "NotificationsEmail",
            },
        ),
    ]
