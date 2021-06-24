import logging
from django.contrib.auth import login, authenticate
from edxmako.shortcuts import render_to_response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from student.models import UserProfile, Registration
from student.models import UserProfile, CourseEnrollment
from django.db.models import Q
from django.conf import settings
from edxmako.shortcuts import render_to_response, render_to_string
from django.core import mail
from celery.task import task
import smtplib
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import authenticate, login as django_login
from student.helpers import authenticate_new_user
from student.views import compose_and_send_activation_email
from django.shortcuts import redirect
from django.urls import reverse
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.custom_programs.models import (
    CustomCourseOverview,
    ProgramAdd,
    ProgramEnrollment,
    ProgramOrder,
    ProgramCoupon,
    CouponRadeemedDetails,
    ProgramCouponRemainUsage,
)

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

log = logging.getLogger("edx.courseware")


@receiver(post_save, sender=ProgramCoupon)
def couponradeemeddetails_post_save(sender, instance, **kwargs):
    remaining_usage = instance.number_of_usage
    couponremain_obj, created = ProgramCouponRemainUsage.objects.get_or_create(
        program_coupon=instance
    )
    if created:
        couponremain_obj.remaining_usage = remaining_usage
        couponremain_obj.save()
    else:
        couponremain_obj.remaining_usage = remaining_usage
        couponremain_obj.save()
    log.info("aanouncement testinggggggggggggggg")
    # find people to email based on `job` instance

    # instance.save()
    log.info("signals calll")
