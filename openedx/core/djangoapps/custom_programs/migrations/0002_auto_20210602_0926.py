# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2021-06-02 13:26
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('custom_programs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CouponRadeemedDetails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('status', models.CharField(blank=True, choices=[(b'initial', b'Initial'), (b'applied', b'applied'), (b'redeemed', b'redeemed'), (b'failed', b'failed')], max_length=255, null=True)),
                ('usage_date', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Coupon Radeemed Details',
                'verbose_name_plural': 'Coupon Radeemed Details',
            },
        ),
        migrations.CreateModel(
            name='ProgramCertificate_Template',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('mode', models.CharField(max_length=255, verbose_name='program_mode')),
                ('template', models.TextField(help_text='Django template HTML.')),
                ('created_date', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
            ],
            options={
                'get_latest_by': 'created_date',
            },
        ),
        migrations.CreateModel(
            name='ProgramCoupon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('coupon_code', models.CharField(max_length=255, verbose_name='coupon_code')),
                ('discout_percentage', models.IntegerField(default=0, verbose_name='Discount Percentage')),
                ('coupon_name', models.CharField(max_length=255, verbose_name='coupon_name')),
                ('coupon_description', models.TextField(default=b'Coupon Description')),
                ('activation_date', models.DateTimeField()),
                ('expiration_date', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('number_of_usage', models.IntegerField(default=0, verbose_name='Number of Usage')),
            ],
            options={
                'ordering': ('coupon_code', 'program'),
            },
        ),
        migrations.CreateModel(
            name='ProgramCouponRemainUsage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('remaining_usage', models.IntegerField(default=0, verbose_name='Remain of Usage')),
                ('program_coupon', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, to='custom_programs.ProgramCoupon')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterModelOptions(
            name='programadd',
            options={'verbose_name': 'Add Programs', 'verbose_name_plural': 'Add Programs'},
        ),
        migrations.AlterField(
            model_name='programorder',
            name='status',
            field=models.CharField(blank=True, choices=[(b'initial', b'Initial'), (b'paying', b'Paying'), (b'paid', b'Paid'), (b'refund', b'Refund')], max_length=255, null=True),
        ),
        migrations.AlterModelTable(
            name='programadd',
            table='AddProgram',
        ),
        migrations.AddField(
            model_name='programcoupon',
            name='program',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, to='custom_programs.ProgramAdd'),
        ),
        migrations.AddField(
            model_name='programcertificate_template',
            name='program',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, to='custom_programs.ProgramAdd'),
        ),
        migrations.AddField(
            model_name='couponradeemeddetails',
            name='coupon',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, to='custom_programs.ProgramCoupon'),
        ),
        migrations.AddField(
            model_name='couponradeemeddetails',
            name='order',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, to='custom_programs.ProgramOrder'),
        ),
        migrations.AddField(
            model_name='couponradeemeddetails',
            name='program',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, to='custom_programs.ProgramAdd'),
        ),
        migrations.AddField(
            model_name='couponradeemeddetails',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='programcoupon',
            unique_together=set([('coupon_code', 'program')]),
        ),
        migrations.AlterUniqueTogether(
            name='programcertificate_template',
            unique_together=set([('name', 'program')]),
        ),
    ]
