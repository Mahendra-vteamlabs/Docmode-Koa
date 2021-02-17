"""
Database ORM models managed by this Django app
Please do not integrate directly with these models!!!  This app currently
offers one programmatic API -- api.py for direct Python integration.
"""

import re
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel
from opaque_keys.edx.keys import CourseKey, UsageKey

# below line imported by docmode to assign assoc admin to view course analytics
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class SponsoringCompany(TimeStampedModel):
    """
    An Organizatio is a representation of an entity which publishes/provides
    one or more courses delivered by the LMS. Organizations have a base set of
    metadata describing the organization, including id, name, and description.
    """

    name = models.CharField(verbose_name="Long name", max_length=255, db_index=True)
    short_name = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    logo_url = models.CharField(max_length=255, db_index=True)
    active = models.BooleanField(default=True)

    class Meta:
        """ Meta class for this Django model """

        verbose_name = _("Sponsoring Company")
        verbose_name_plural = _("Sponsoring Company")

    def __unicode__(self):
        return u"{}".format(self.name)


class Organization(TimeStampedModel):
    """
    An Organization is a representation of an entity which publishes/provides
    one or more courses delivered by the LMS. Organizations have a base set of
    metadata describing the organization, including id, name, and description.
    """

    class Meta:
        """ Meta class for this Django model """

        verbose_name = _("Associations")
        verbose_name_plural = _("Associations")

    name = models.CharField(max_length=255, db_index=True)
    short_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Short Name",
        help_text=_(
            "Please do not use spaces or special characters. Only allowed special characters "
            "are period (.), hyphen (-) and underscore (_)."
        ),
    )
    description = models.TextField(null=True, blank=True)
    logo = models.CharField(max_length=255, null=True)
    sponsoring_company = models.ForeignKey(
        SponsoringCompany, db_index=True, null=True, on_delete=models.CASCADE
    )
    active = models.BooleanField(default=True)
    homepage_in_network_with = models.BooleanField(default=False)
    org_promo_video = models.CharField(max_length=555, null=True, blank=True)
    marketing_display = models.BooleanField(default=True)

    def __unicode__(self):
        return u"{name} ({short_name})".format(
            name=self.name, short_name=self.short_name
        )

    def clean(self):
        if not re.match("^[a-zA-Z0-9._-]*$", self.short_name):
            raise ValidationError(
                _(
                    "Please do not use spaces or special characters in the short name "
                    "field. Only allowed special characters are period (.), hyphen (-) "
                    "and underscore (_)."
                )
            )


class OrganizationCourse(TimeStampedModel):
    """
    An OrganizationCourse represents the link between an Organization and a
    Course (via course key). Because Courses are not true Open edX entities
    (in the Django/ORM sense) the modeling and integrity is limited to that
    of specifying course identifier strings in this model.
    """

    course_id = models.CharField(
        max_length=255, db_index=True, verbose_name="Course ID"
    )
    organization = models.ForeignKey(
        Organization, db_index=True, on_delete=models.CASCADE
    )
    active = models.BooleanField(default=True)

    class Meta(object):
        """ Meta class for this Django model """

        unique_together = (("course_id", "organization"),)
        verbose_name = _("Link Course")
        verbose_name_plural = _("Link Courses")


class OrganizationSlider(TimeStampedModel):
    """
    An Organizatio is a representation of an entity which publishes/provides
    one or more courses delivered by the LMS. Organizations have a base set of
    metadata describing the organization, including id, name, and description.
    """

    organization = models.ForeignKey(
        Organization, db_index=True, on_delete=models.CASCADE
    )
    active = models.BooleanField(default=True)
    image_s3_urls = models.TextField(null=True)

    class Meta:
        """ Meta class for this Django model """

        verbose_name = _("Association Sliders")
        verbose_name_plural = _("Association Sliders")

    def __unicode__(self):
        return u"{}".format(self.organization)


class OrgShortCode(TimeStampedModel):
    """
    An Organizatio is a representation of an entity which publishes/provides
    one or more courses delivered by the LMS. Organizations have a base set of
    metadata describing the organization, including id, name, and description.
    """

    code = models.CharField(max_length=10, db_index=True)
    organization = models.ForeignKey(
        Organization, db_index=True, on_delete=models.CASCADE
    )

    class Meta:
        """ Meta class for this Django model """

        verbose_name = _("Association Shortcodes")
        verbose_name_plural = _("Association Shortcodes")

    def __unicode__(self):
        return u"{}".format(self.organization)


class OrganizationMembers(TimeStampedModel):
    """
    An Organizatio is a representation of an entity which publishes/provides
    one or more courses delivered by the LMS. Organizations have a base set of
    metadata describing the organization, including id, name, and description.
    """

    user_id = models.CharField(max_length=10, db_index=True)
    user_email = models.CharField(max_length=255, db_index=True, null=True)
    is_admin = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    organization = models.ForeignKey(
        Organization, db_index=True, on_delete=models.CASCADE
    )
    course_ids = models.CharField(db_index=True, max_length=500)

    class Meta:
        """ Meta class for this Django model """

        verbose_name = _("Association Members")
        verbose_name_plural = _("Association Members")

    def __unicode__(self):
        return u"{}".format(self.user_id)


class Organization_sub_admins(TimeStampedModel):
    user_email = models.CharField(max_length=255, db_index=True, null=True)
    is_admin = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    organization = models.ForeignKey(
        Organization, db_index=True, on_delete=models.CASCADE
    )
    course_id = models.CharField(db_index=True, max_length=500)
    state_ids = models.CharField(db_index=True, max_length=500)

    class Meta:
        """ Meta class for this Django model """

        verbose_name = _("Association Sub Admin")
        verbose_name_plural = _("Association Subadmin")

    def __unicode__(self):
        return u"{}".format(self.user_email)
