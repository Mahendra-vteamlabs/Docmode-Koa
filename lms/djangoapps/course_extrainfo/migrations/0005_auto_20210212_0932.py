# Generated by Django 2.2.18 on 2021-02-12 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("course_extrainfo", "0004_auto_20190903_0403"),
    ]

    operations = [
        migrations.AlterField(
            model_name="course_extrainfo",
            name="course_type",
            field=models.CharField(max_length=2, verbose_name="Course_type"),
        ),
    ]
