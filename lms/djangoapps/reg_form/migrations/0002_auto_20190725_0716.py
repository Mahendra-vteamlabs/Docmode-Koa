# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-07-25 11:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reg_form", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="extrafields",
            name="education",
            field=models.CharField(blank=True, max_length=250),
        ),
        migrations.AddField(
            model_name="extrafields",
            name="medical_philosophy",
            field=models.CharField(blank=True, max_length=150),
        ),
    ]
