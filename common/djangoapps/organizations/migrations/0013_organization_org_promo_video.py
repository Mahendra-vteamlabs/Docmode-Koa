# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-07-23 06:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0012_auto_20190305_0158"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="org_promo_video",
            field=models.CharField(blank=True, max_length=555, null=True),
        ),
    ]
