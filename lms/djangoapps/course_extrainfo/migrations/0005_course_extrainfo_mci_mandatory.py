# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2020-06-22 05:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("course_extrainfo", "0004_auto_20190903_0403"),
    ]

    operations = [
        migrations.AddField(
            model_name="course_extrainfo",
            name="mci_mandatory",
            field=models.CharField(blank=True, default=0, max_length=2),
        ),
    ]
