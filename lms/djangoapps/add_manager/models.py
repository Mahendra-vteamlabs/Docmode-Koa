from datetime import datetime
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from common.djangoapps.organizations.models import SponsoringCompany, Organization

USER_MODEL = getattr(settings, "AUTH_USER_MODEL", "auth.User")

# Create your models here.


class Sponsored_course_users(models.Model):
    course_id = models.CharField(max_length=255, db_index=True)
    sponsoringcompany = models.CharField(max_length=20, db_index=True, null=True)
    image_url = models.CharField(max_length=250, blank=True)
    video_url = models.CharField(max_length=250, blank=True)
    coupon_code = models.TextField(null=False)
    question = models.CharField(max_length=250, blank=True)
    answer = models.CharField(max_length=250, blank=True)

    def __unicode__(self):
        return self.course_id


class associations_ad_manager(models.Model):
    course_id = models.CharField(
        max_length=255, db_index=True, verbose_name="Course ID"
    )
    organization = models.ForeignKey(Organization, db_index=True)
    image_url = models.CharField(max_length=250, blank=True)
    video_url = models.CharField(max_length=250, blank=True)
    disclaimer = models.TextField(blank=True)
    date = models.DateTimeField(default=datetime.now, blank=True)

    class Meta(object):
        """ Meta class for this Django model """

        verbose_name = _("Association ad")
        verbose_name_plural = _("Associations ads")


class user_view_counter(models.Model):
    course_id = models.CharField(max_length=255, db_index=True)
    counter = models.CharField(max_length=255, db_index=True)
    mcounter = models.CharField(max_length=255, null=True)
    user = models.ForeignKey(USER_MODEL, null=True)

    def __unicode__(self):
        return self.course_id


class disclaimer_agreement_status(models.Model):
    course_id = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=255, default=0)
    user = models.ForeignKey(USER_MODEL, null=True)

    def __unicode__(self):
        return self.course_id
