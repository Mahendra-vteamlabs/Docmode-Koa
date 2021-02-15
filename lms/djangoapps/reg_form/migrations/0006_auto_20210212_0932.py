# Generated by Django 2.2.18 on 2021-02-12 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reg_form", "0005_auto_20200511_0827"),
    ]

    operations = [
        migrations.AlterField(
            model_name="extrafields",
            name="medical_philosophy",
            field=models.CharField(
                blank=True,
                default="He who studies medicine without books sails an uncharted sea, but he who studies medicine without patients does not go to sea at all.",
                max_length=350,
            ),
        ),
        migrations.AlterField(
            model_name="extrafields",
            name="reg_num",
            field=models.CharField(max_length=100, verbose_name="Reg Num"),
        ),
        migrations.AlterField(
            model_name="extrafields",
            name="user_type",
            field=models.CharField(
                choices=[
                    ("dr", "Doctor"),
                    ("u", "User"),
                    ("ms", "Medical Student"),
                    ("hc", "Health Care Professional"),
                ],
                db_index=True,
                default="dr",
                max_length=2,
            ),
        ),
    ]
