# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-08-06 06:28
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("push_notification", "0003_remove_docmodenotification_users"),
    ]

    operations = [
        migrations.AddField(
            model_name="docmodenotification",
            name="users",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
