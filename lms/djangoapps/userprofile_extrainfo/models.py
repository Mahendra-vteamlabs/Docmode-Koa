# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class education(models.Model):
    user = models.CharField(blank=False, max_length=255)
    year = models.PositiveSmallIntegerField(null=True)
    institution_name = models.CharField(blank=False, max_length=255)
    certificate_path = models.CharField(blank=True, max_length=555)
    description = models.CharField(blank=True, max_length=555)

    def __str__(self):
        return "{}".format(self.user)


class awards(models.Model):
    user = models.CharField(blank=False, max_length=255)
    title = models.CharField(blank=False, max_length=255)
    year = models.PositiveSmallIntegerField(null=True)
    award_image_path = models.CharField(blank=True, max_length=555)

    def __str__(self):
        return "{}".format(self.user)


class research_papers(models.Model):
    user = models.CharField(blank=False, max_length=255)
    title = models.CharField(blank=False, max_length=255)
    description = models.CharField(blank=True, max_length=555)
    pdf_path = models.CharField(blank=True, max_length=555)
    extarnal_link = models.CharField(blank=False, max_length=255)

    def __str__(self):
        return "{}".format(self.user)


class media_featured(models.Model):
    user = models.CharField(blank=False, max_length=255)
    title = models.CharField(blank=False, max_length=255)
    media_name = models.CharField(blank=True, max_length=555)
    media_link = models.CharField(blank=False, max_length=255)
    img = models.CharField(blank=True, max_length=555)

    def __str__(self):
        return "{}".format(self.user)


class clinic_hospital_address(models.Model):
    user = models.CharField(blank=False, max_length=255)
    clinic_hospital_name = models.CharField(blank=False, max_length=255)
    address_line1 = models.CharField(blank=True, max_length=1000)
    address_line2 = models.CharField(blank=True, max_length=1000)
    address_line3 = models.CharField(blank=True, max_length=1000)
    phone_number = models.CharField(blank=True, max_length=25)
    website = models.CharField(blank=True, max_length=255)
    timings = models.CharField(blank=True, max_length=100)

    def __str__(self):
        return "{}".format(self.user)


class healthcare_awareness_videos(models.Model):
    user = models.CharField(blank=False, max_length=255)
    video_url = models.CharField(blank=False, max_length=500)
    active = models.CharField(blank=False, max_length=10)

    def __str__(self):
        return "{}".format(self.user)


class experience(models.Model):
    user = models.CharField(blank=False, max_length=255)
    year = models.CharField(blank=False, max_length=255)
    institution_name = models.CharField(blank=False, max_length=255)
    description = models.CharField(blank=True, max_length=555)

    def __str__(self):
        return "{}".format(self.user)
