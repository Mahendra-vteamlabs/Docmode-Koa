import logging
from django.db import models
from jsonfield import JSONField
from django.contrib.auth.models import User, Permission
from django.utils import six, timezone
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator

from django.contrib.auth.validators import (
    ASCIIUsernameValidator,
    UnicodeUsernameValidator,
)
from django.contrib.auth.models import User

from openedx.core.djangoapps.lang_pref.api import all_languages
from opaque_keys.edx.django.models import CourseKeyField
from model_utils.models import TimeStampedModel
from django.contrib.sites.models import Site
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


STATUS_TYPE = (
    ("initial", "Initial"),
    ("paying", "Paying"),
    ("paid", "Paid"),
    ("refund", "Refund"),
)


COUPON_STATUS_TYPE = (
    ("initial", "Initial"),
    ("applied", "applied"),
    ("redeemed", "redeemed"),
    ("failed", "failed"),
)


class CustomCourseOverview(TimeStampedModel):
    course_id = CourseKeyField(max_length=255, db_index=True)
    name = models.CharField(null=True, blank=True, max_length=255)

    def __str__(self):
        return self.name


class ProgramAdd(TimeStampedModel):

    name = models.CharField(_("program_name"), max_length=255)
    program_image = models.ImageField(
        upload_to="program_images/", null=False, blank=False
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    enrollment_start_date = models.DateTimeField()
    enrollment_end_date = models.DateTimeField()
    short_description = models.TextField(
        null=False, blank=False, default="describe budle details"
    )
    price = models.IntegerField(default=0, verbose_name=_("Price"))
    currency = models.CharField(_("currency"), max_length=255)
    efforts = models.CharField(_("efforts"), max_length=255)
    site = models.ForeignKey(Site, null=True, on_delete=models.CASCADE)
    courses = models.ManyToManyField(CustomCourseOverview, related_name="programaddes")

    def __str__(self):
        return self.name

    class Meta:
        db_table = "AddProgram"
        verbose_name = _("Add Programs")
        verbose_name_plural = _("Add Programs")


class ProgramEnrollment(TimeStampedModel):
    """
    Model for storing user with bundle enrollment
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="program_enroll_user")
    program = models.ForeignKey(
        ProgramAdd,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
    )

    class Meta(object):
        unique_together = (("user", "program"),)
        ordering = ("user", "program")


class ProgramOrder(TimeStampedModel):
    """
    Model for storing user with bundle enrollment
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    program = models.ForeignKey(
        ProgramAdd,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
    )
    item_name = models.CharField(_("item_name"), max_length=255)
    price = models.IntegerField(default=0, verbose_name=_("Price"))
    currency = models.CharField(_("currency"), max_length=255)
    discount_price = models.IntegerField(default=0, verbose_name=_("Discount Price"))
    status = models.CharField(
        null=True, blank=True, max_length=255, choices=STATUS_TYPE
    )
    payment_id = models.CharField(_("payment reciept numnber"), max_length=255)
    payment_reference = models.CharField(_("payment_reference"), max_length=255)
    payment_response = JSONField()

    def __str__(self):
        return self.item_name


class ProgramCoupon(TimeStampedModel):

    program = models.ForeignKey(
        ProgramAdd,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
    )
    coupon_code = models.CharField(_("coupon_code"), max_length=255)
    discout_percentage = models.IntegerField(
        default=0, verbose_name=_("Discount Percentage")
    )
    coupon_name = models.CharField(_("coupon_name"), max_length=255)
    coupon_description = models.TextField(
        null=False, blank=False, default="Coupon Description"
    )
    activation_date = models.DateTimeField()
    expiration_date = models.DateTimeField()
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    number_of_usage = models.IntegerField(default=0, verbose_name=_("Number of Usage"))
    # remaining_usage = models.IntegerField(default=0, verbose_name=_("Remain of Usage"))
    def __str__(self):
        return self.coupon_code

    class Meta(object):
        unique_together = (("coupon_code", "program"),)
        ordering = ("coupon_code", "program")


class ProgramCouponRemainUsage(TimeStampedModel):
    program_coupon = models.ForeignKey(
        ProgramCoupon,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
    )
    remaining_usage = models.IntegerField(default=0, verbose_name=_("Remain of Usage"))


class CouponRadeemedDetails(TimeStampedModel):

    order = models.ForeignKey(
        ProgramOrder,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
    )
    program = models.ForeignKey(
        ProgramAdd,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
    )
    coupon = models.ForeignKey(
        ProgramCoupon,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        null=True, blank=True, max_length=255, choices=COUPON_STATUS_TYPE
    )
    usage_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Coupon Radeemed Details")
        verbose_name_plural = _("Coupon Radeemed Details")


class ProgramCertificate_Template(TimeStampedModel):

    name = models.CharField(_("name"), max_length=255)
    program = models.ForeignKey(
        ProgramAdd,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
    )
    mode = models.CharField(_("program_mode"), max_length=255)
    template = models.TextField(
        help_text=_(u"Django template HTML."),
    )
    created_date = models.DateTimeField()
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))

    def __str__(self):
        return self.name

    class Meta(object):
        get_latest_by = "created_date"
        unique_together = (("name", "program"),)
