# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2020-06-22 05:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reg_form", "0006_auto_20200605_0153"),
    ]

    operations = [
        migrations.AlterField(
            model_name="extrafields",
            name="rpincode",
            field=models.CharField(blank=True, db_index=True, max_length=10),
        ),
    ]
