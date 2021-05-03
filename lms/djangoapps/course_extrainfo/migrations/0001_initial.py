# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-28 11:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("specialization", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="course_extrainfo",
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
                ("course_id", models.CharField(db_index=True, max_length=255)),
                (
                    "course_type",
                    models.CharField(max_length=2, verbose_name=b"Course_type"),
                ),
                ("category", models.CharField(db_index=True, max_length=2, null=True)),
                (
                    "sub_category",
                    models.CharField(db_index=True, max_length=150, null=True),
                ),
                (
                    "specialization",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="specialization.specializations",
                    ),
                ),
            ],
        ),
    ]
